use serde::{Deserialize, Serialize};

use crate::error::PlatformError;
use crate::media::MediaInspection;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct MasteringTarget {
    pub profile: String,
    pub target_lufs: f64,
    pub target_true_peak_dbtp: f64,
    pub preferred_lra_min_lu: f64,
    pub preferred_lra_max_lu: f64,
    pub loudness_tolerance_lu: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct MasteringDecision {
    pub source: MediaInspection,
    pub target: MasteringTarget,
    pub loudness_delta_db: Option<f64>,
    pub action: String,
    pub auto_mastering_allowed: bool,
    pub requires_review: bool,
    pub quality_flags: Vec<String>,
    pub reasons: Vec<String>,
}

pub fn mastering_target(profile: &str) -> Result<MasteringTarget, PlatformError> {
    let target = match profile {
        "music-balanced" => MasteringTarget {
            profile: profile.into(),
            target_lufs: -14.0,
            target_true_peak_dbtp: -1.0,
            preferred_lra_min_lu: 2.5,
            preferred_lra_max_lu: 14.0,
            loudness_tolerance_lu: 0.7,
        },
        "music-loud" => MasteringTarget {
            profile: profile.into(),
            target_lufs: -10.0,
            target_true_peak_dbtp: -1.0,
            preferred_lra_min_lu: 1.5,
            preferred_lra_max_lu: 10.0,
            loudness_tolerance_lu: 0.7,
        },
        "speech" => MasteringTarget {
            profile: profile.into(),
            target_lufs: -16.0,
            target_true_peak_dbtp: -1.0,
            preferred_lra_min_lu: 1.0,
            preferred_lra_max_lu: 12.0,
            loudness_tolerance_lu: 0.7,
        },
        other => {
            return Err(PlatformError::Validation(format!(
                "unsupported mastering analysis profile: {other}"
            )));
        }
    };
    Ok(target)
}

pub fn decide_mastering(
    inspection: &MediaInspection,
    profile: &str,
) -> Result<MasteringDecision, PlatformError> {
    let target = mastering_target(profile)?;
    let mut flags = Vec::new();
    let mut reasons = Vec::new();

    let loudness_delta_db = inspection
        .integrated_lufs
        .map(|measured| target.target_lufs - measured);

    if inspection.integrated_lufs.is_none() {
        flags.push("unmeasurable_integrated_loudness".into());
        reasons.push("Integrated loudness is below the EBU R128 measurement floor.".into());
    }
    if inspection.true_peak_dbtp.is_none() {
        flags.push("unmeasurable_true_peak".into());
        reasons.push("True peak is below the measurement floor.".into());
    }
    if inspection.duration_seconds < 5.0 {
        flags.push("short_program".into());
        reasons.push(
            "Program is shorter than 5 seconds; mastering metrics are less representative.".into(),
        );
    }
    if inspection.sample_rate_hz < 44_100 {
        flags.push("sample_rate_below_delivery_floor".into());
        reasons.push("Sample rate is below the 44.1 kHz delivery floor.".into());
    }
    if inspection.channels > 2 {
        flags.push("multichannel_requires_review".into());
        reasons.push(
            "The current automatic mastering path is validated for mono/stereo material only."
                .into(),
        );
    }
    if inspection.loudness_range_lu < target.preferred_lra_min_lu {
        flags.push("dynamics_below_preferred_range".into());
        reasons.push(format!(
            "Measured LRA {:.1} LU is below the preferred {:.1} LU floor for {}.",
            inspection.loudness_range_lu, target.preferred_lra_min_lu, target.profile
        ));
    }
    if inspection.loudness_range_lu > target.preferred_lra_max_lu {
        flags.push("dynamics_above_preferred_range".into());
        reasons.push(format!(
            "Measured LRA {:.1} LU exceeds the preferred {:.1} LU ceiling for {}.",
            inspection.loudness_range_lu, target.preferred_lra_max_lu, target.profile
        ));
    }

    if let Some(peak) = inspection.true_peak_dbtp {
        if peak > -0.1 {
            flags.push("likely_clipping_or_zero_headroom".into());
            reasons.push(format!(
                "Measured true peak {peak:.2} dBTP leaves effectively no mastering headroom."
            ));
        } else if peak > target.target_true_peak_dbtp + 0.1 {
            flags.push("true_peak_above_target_ceiling".into());
            reasons.push(format!(
                "Measured true peak {peak:.2} dBTP exceeds the {:.2} dBTP target ceiling.",
                target.target_true_peak_dbtp
            ));
        }
    }

    if let (Some(measured), Some(delta)) = (inspection.integrated_lufs, loudness_delta_db)
        && delta.abs() > target.loudness_tolerance_lu
    {
        flags.push("loudness_outside_target_tolerance".into());
        reasons.push(format!(
            "Measured loudness {measured:.2} LUFS differs from the {:.2} LUFS target by {delta:.2} dB.",
            target.target_lufs
        ));
    }

    let requires_review = flags.iter().any(|flag| {
        matches!(
            flag.as_str(),
            "unmeasurable_integrated_loudness"
                | "unmeasurable_true_peak"
                | "sample_rate_below_delivery_floor"
                | "multichannel_requires_review"
                | "dynamics_below_preferred_range"
                | "dynamics_above_preferred_range"
                | "likely_clipping_or_zero_headroom"
        )
    });

    let needs_level_change = loudness_delta_db
        .is_some_and(|delta| delta.abs() > target.loudness_tolerance_lu)
        || inspection
            .true_peak_dbtp
            .is_some_and(|peak| peak > target.target_true_peak_dbtp + 0.1);

    let action = if requires_review {
        "review_before_mastering"
    } else if needs_level_change {
        "normalize_loudness"
    } else {
        "preserve"
    }
    .to_owned();

    let auto_mastering_allowed = !requires_review
        && inspection.integrated_lufs.is_some()
        && inspection.true_peak_dbtp.is_some();

    if reasons.is_empty() {
        reasons
            .push("Technical metrics are inside the selected mastering profile envelope.".into());
    }

    Ok(MasteringDecision {
        source: inspection.clone(),
        target,
        loudness_delta_db,
        action,
        auto_mastering_allowed,
        requires_review,
        quality_flags: flags,
        reasons,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn inspection(lufs: f64, peak: f64, lra: f64) -> MediaInspection {
        MediaInspection {
            duration_seconds: 180.0,
            sample_rate_hz: 48_000,
            channels: 2,
            codec: "pcm_s24le".into(),
            integrated_lufs: Some(lufs),
            integrated_lufs_status: "measured".into(),
            loudness_range_lu: lra,
            true_peak_dbtp: Some(peak),
            true_peak_status: "measured".into(),
        }
    }

    #[test]
    fn balanced_material_is_preserved() {
        let decision =
            decide_mastering(&inspection(-14.2, -1.2, 7.0), "music-balanced").expect("decision");
        assert_eq!(decision.action, "preserve");
        assert!(decision.auto_mastering_allowed);
        assert!(!decision.requires_review);
    }

    #[test]
    fn quiet_but_healthy_material_can_be_normalized_automatically() {
        let decision =
            decide_mastering(&inspection(-20.0, -6.0, 8.0), "music-balanced").expect("decision");
        assert_eq!(decision.action, "normalize_loudness");
        assert!(decision.auto_mastering_allowed);
        assert!(
            decision
                .quality_flags
                .iter()
                .any(|flag| flag == "loudness_outside_target_tolerance")
        );
    }

    #[test]
    fn clipped_or_extreme_dynamics_require_review() {
        let decision =
            decide_mastering(&inspection(-7.0, -0.02, 0.5), "music-balanced").expect("decision");
        assert_eq!(decision.action, "review_before_mastering");
        assert!(!decision.auto_mastering_allowed);
        assert!(decision.requires_review);
        assert!(
            decision
                .quality_flags
                .iter()
                .any(|flag| flag == "likely_clipping_or_zero_headroom")
        );
    }

    #[test]
    fn unsupported_profile_is_rejected() {
        let error = decide_mastering(&inspection(-14.0, -1.0, 6.0), "magic")
            .expect_err("unsupported profile must fail");
        assert!(matches!(error, PlatformError::Validation(_)));
    }
}
