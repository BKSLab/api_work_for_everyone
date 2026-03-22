# Design Guide — Работа для всех

Гайдлайн по визуальному стилю проекта. Используется как референс при разработке новых интерфейсов — в том числе админки (sqladmin).

---

## Общая концепция

**Тёмная тема, золотой акцент.** Никакой светлой темы — только dark-first.

Визуальный язык: минималистичный, технологичный, с тонким ощущением премиальности. Не агрессивный, не кричащий. Золото используется точечно — только для акцентов и интерактивных элементов, не для фонов.

Целевая аудитория — люди с инвалидностью, поэтому доступность (WCAG 2.2 AA) — не опция, а требование.

---

## Цветовая палитра

### Базовые токены

| Токен               | HEX       | Применение |
|---------------------|-----------|------------|
| `--background`      | `#0A0A0A` | Фон страницы (почти чёрный) |
| `--surface`         | `#1A1A1A` | Фон карточек, инпутов, панелей |
| `--surface-hover`   | `#252525` | Hover-состояние поверхностей |
| `--border`          | `#2D2D2D` | Все границы и разделители |
| `--foreground`      | `#F0F0F0` | Основной текст |
| `--muted`           | `#999999` | Вторичный текст, плейсхолдеры, подписи |
| `--accent`          | `#F5B800` | Главный акцент — золото |
| `--accent-hover`    | `#E0A800` | Hover на акцентных элементах |
| `--accent-foreground` | `#0A0A0A` | Текст поверх акцентного фона (чёрный) |

### Служебные цвета

Не являются CSS-переменными, используются как Tailwind-классы:

| Цвет | Применение |
|------|------------|
| `red-400` / `red-400/20` | Ошибки, предупреждения безопасности |
| `blue-400` / `blue-400/20` | Бейдж источника «Работа России» |
| `red-400/20` + `red-400` | Бейдж источника hh.ru |
| `white/10`, `white/20` | Подложки кнопок secondary |
| `white/10`, `white/12` | Стеклянные поверхности (glassmorphism) |

### Принципы работы с цветом

- Акцент (`#F5B800`) — только для интерактивных элементов, иконок AI-функций, важных меток. Никогда не красить им большие фоновые области.
- Полупрозрачность акцента — для подсветок, рамок, теней: `accent/10`, `accent/30`, `accent/50`, `accent/60`.
- Свечение через `box-shadow`: `0 0 24px rgba(245,184,0,0.12)` — subtle glow на hover.
- Текст делится на два уровня: `foreground` (основной) и `muted` (вторичный). Третьего уровня нет.

---

## Типографика

**Шрифт:** Geist Sans (Google Fonts, загружается через `next/font`). Для кода и OTP — `Courier, monospace`.

### Шкала размеров (практическая)

| Роль | Класс / размер |
|------|---------------|
| Заголовок страницы | `text-2xl font-bold` или `text-3xl font-bold` |
| Заголовок карточки | `text-xl font-bold` |
| Заголовок секции | `text-base font-semibold` |
| Основной текст | `text-sm` (14px) |
| Вторичный текст | `text-sm text-muted` |
| Мелкие подписи, бейджи | `text-xs` (12px) |
| Микро-метки (uppercase) | `text-[9px]` или `text-[11px]` + `tracking-wider uppercase` |

### Принципы

- `font-semibold` — для меток и кнопок.
- `font-bold` / `font-extrabold` — только заголовки.
- Межстрочный интервал: `leading-relaxed` (1.625) для длинного текста, `leading-tight` для компактных блоков.
- Акцентные заголовки (как «Вера» в письмах): `font-black`, `letter-spacing: 0.04em`.

---

## Интерактивные элементы

### Кнопка Primary

```
bg-accent text-accent-foreground (чёрный текст на золотом фоне)
hover:bg-accent-hover
rounded px-4 py-2 font-semibold
focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent
disabled:opacity-60 disabled:cursor-not-allowed
```

### Кнопка Secondary (основная для большинства действий)

```
border border-accent/50 bg-white/10 text-accent
hover:border-accent hover:bg-white/20
rounded px-3 py-1.5 text-sm font-semibold
focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent
disabled:opacity-60 disabled:cursor-not-allowed
```

### Кнопка Neutral (выход, неважные действия)

```
bg-surface-hover text-foreground
hover:bg-border
rounded px-3 py-1.5 text-sm font-medium
```

### Правила кнопок

- Всегда `focus-visible:outline-accent` — скринридеры и клавиатурная навигация.
- Никогда `outline-none` без альтернативы.
- Состояние disabled — через `opacity-60`, не через скрытие.

---

## Поля ввода (inputs, textarea)

```
rounded border border-border bg-surface px-3 py-2
text-foreground placeholder:text-muted
focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent
aria-invalid → визуально ничего дополнительного не меняем, ошибка — отдельным текстом
```

Ошибки поля — `text-sm text-red-400`, с `role="alert"` и `aria-describedby`.

---

## Карточки и поверхности

### Стандартная карточка

```
rounded-lg border border-white/20 bg-surface p-6
```

### Карточка с акцентным свечением (например, вакансии)

```
rounded-lg border border-white/20 bg-surface
bg-[radial-gradient(circle_at_top_left,rgba(245,184,0,0.07),transparent_50%)] p-6
```

### Стеклянный блок (glassmorphism — для лого, оверлеев)

```
border border-white/15
bg-[linear-gradient(135deg,rgba(255,255,255,0.08),rgba(255,255,255,0.03))]
backdrop-blur-md
```

### Информационный блок (подсказки, уведомления)

```
background: #171700  border: 1px solid #2D2800  border-radius: 12px
```
Это `bg-[#171700] border border-[#2D2800] rounded-xl` — тёмно-жёлтый оттенок фона, едва заметный.

### Hover на карточках

```
hover:border-accent/30 hover:shadow-[0_0_24px_rgba(245,184,0,0.12)]
```

---

## Разделители и границы

- Горизонтальные линии: `border-t border-border` или `border-t-2 border-accent` (акцентный разделитель под заголовком карточки).
- Между элементами списков: `divide-y divide-white/8`.
- Жёлтая полоска сверху (в письмах, модалах): `height: 3px; background: #F5B800`.

---

## Шапка (Header)

- `sticky top-0 z-40`
- `bg-background/60 backdrop-blur-md backdrop-saturate-150` — полупрозрачная с blur
- `border-b border-white/10`
- Навигационные ссылки: `text-sm text-muted hover:text-foreground transition-colors`
- Активная страница — визуально не выделяется через цвет (только через aria-current если нужно)

---

## Бейджи и метки

### Бейдж источника

```
hh.ru:           bg-red-400/20  text-red-400
Работа России:   bg-blue-400/20 text-blue-400
default:         bg-border      text-muted
```
Размер: `text-xs px-2 py-0.5 rounded`

### AI-метка

```
border border-accent/30 bg-accent/10
text-accent/80 text-[9px] font-semibold uppercase tracking-wider
rounded-full px-1.5 py-px
```

### Метка-капслок (карьерный консультант и др.)

```
text-[11px] uppercase tracking-widest color: #7A5E00 или text-muted
```

---

## Состояния загрузки и пустые состояния

- Спиннер: простой SVG-круг с `animate-spin`, цвет `text-accent`.
- Скелетон: `bg-surface animate-pulse rounded`.
- Пустое состояние: иконка + заголовок `text-foreground` + подпись `text-muted`.

---

## Доступность (обязательно)

- Все интерактивные элементы имеют видимый `focus-visible` — `outline-2 outline-offset-2 outline-accent`.
- `aria-label` на иконочных кнопках без текста.
- `aria-required`, `aria-invalid`, `aria-describedby` на полях форм.
- `role="alert"` на сообщениях об ошибках.
- `aria-live="polite"` на динамических регионах.
- Чисто визуальные декоративные элементы: `aria-hidden="true"`.
- Скринридер-текст: `className="sr-only"`.
- Контраст: основной текст `#F0F0F0` на `#0A0A0A` — 18.1:1 (AAA). Акцент `#F5B800` на `#0A0A0A` — 10.5:1 (AAA).

---

## Sqladmin — применение стиля

При кастомизации sqladmin приоритеты следующие:

1. **Фон и поверхности** — заменить белые/светло-серые на `#0A0A0A` / `#1A1A1A`.
2. **Акцент** — заменить синий Bootstrap на `#F5B800`. Hover — `#E0A800`.
3. **Навбар** — `background: #1A1A1A`, `border-bottom: 1px solid #2D2D2D`.
4. **Таблицы** — чередование строк: `#0A0A0A` / `#111111`, hover строки: `#1A1A1A`.
5. **Кнопки** — primary: золото с чёрным текстом; secondary: прозрачный с золотой рамкой.
6. **Формы** — `background: #1A1A1A`, `border: 1px solid #2D2D2D`, `color: #F0F0F0`, focus: `border-color: #F5B800; box-shadow: 0 0 0 2px rgba(245,184,0,0.25)`.
7. **Sidebar** — `background: #111111`, активный пункт: `background: rgba(245,184,0,0.1); color: #F5B800; border-left: 2px solid #F5B800`.
8. **Алерты** — success: зелёный остаётся; danger: `red-400`; info: заменить синий на `accent/20 + accent`.
