# Cost Policy

- По умолчанию использовать уже оплаченный Chat и локальные open-source tools.
- Не добавлять платный LLM/API для задачи, которую закрывает текущий Chat.
- Платный executor допускается только при измеримом quality/capacity gap.
- Сравнивать total cost: лицензия, API, compute, установка, обслуживание и ручной труд.
- Не держать постоянный GPU/VPS/workflow SaaS без устойчивой загрузки.
- Любой monetary side effect выше нуля проходит policy; превышение лимита guarded.

