---
name: "Colibri LOOK"
description: "Светлый fashion-каталог по референсу Anvogue с реальными фотографиями и видео бутика."
colors:
  paper: "#fff"
  ink: "#202020"
  dark: "#171717"
  muted: "#626262"
  surface: "#f5f5f5"
  accent: "#e3eacb"
  hero: "#eceae5"
  button-hover: "#42483a"
  field-border: "#dedede"
  divider: "#e4e4e4"
  atelier: "#f0f0ed"
  scrollbar-thumb: "#b5b5b5"
  admin-primary: "#4e3b25"
  admin-dark: "#171512"
  admin-link: "#725230"
  admin-default-hover: "#6c5134"
  admin-selected-row: "#ede3d5"
  admin-paper: "#f3f2ee"
  admin-scrollbar-thumb: "#777972"
  admin-scrollbar-track: "#e8e7e1"
typography:
  display:
    fontFamily: "Golos, Arial, sans-serif"
    fontSize: "clamp(46px, 5vw, 72px)"
    fontWeight: 500
    lineHeight: 1.08
    letterSpacing: "-0.04em"
  page-title:
    fontFamily: "Golos, Arial, sans-serif"
    fontSize: "clamp(38px, 4vw, 56px)"
    fontWeight: 500
    lineHeight: 1.15
    letterSpacing: "-0.035em"
  headline:
    fontFamily: "Golos, Arial, sans-serif"
    fontSize: "clamp(30px, 3vw, 42px)"
    fontWeight: 500
    lineHeight: 1.15
    letterSpacing: "-0.035em"
  body:
    fontFamily: "Golos, Arial, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.6
  product-title:
    fontFamily: "Golos, Arial, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "Golos, Arial, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.6
  button:
    fontFamily: "Golos, Arial, sans-serif"
    fontSize: "14px"
    fontWeight: 500
    lineHeight: 1.4
  admin-body:
    fontFamily: "Golos, Arial, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.5
  admin-brand:
    fontFamily: "Oswald, Georgia, serif"
    fontSize: "32px"
rounded:
  control: "5px"
  card: "10px"
  category: "12px"
  mobile-card: "7px"
  mobile-panel: "8px"
  tab: "24px"
  tabs-container: "28px"
  round: "50%"
spacing:
  gutter: "clamp(20px, 5.2vw, 80px)"
  section: "80px"
  tablet-section: "64px"
  phone-section: "52px"
components:
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
    typography: "{typography.button}"
    rounded: "{rounded.control}"
    padding: "14px 26px"
  button-light:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    typography: "{typography.button}"
    rounded: "{rounded.control}"
    padding: "14px 26px"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.button}"
    rounded: "{rounded.control}"
    padding: "14px 26px"
  catalog-input:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "0 12px"
    height: "48px"
  product-label:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "4px 9px"
  size-button:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "12px 18px"
  size-button-selected:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
    rounded: "{rounded.control}"
    padding: "12px 18px"
  collection-tab:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    rounded: "{rounded.tab}"
    padding: "10px 20px"
  collection-tab-selected:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.tab}"
    padding: "10px 20px"
---

# Design System: Colibri LOOK

## Overview

**Creative North Star: "Светлая fashion-витрина по Anvogue"**

Текущая визуальная authority — явно предоставленный пользователем [референс Anvogue](https://bootstraptema.ru/_sf/67/6736.html), его [живое демо](https://anvogue-html.vercel.app/). Реализована светлая магазинная композиция: белая шапка без верхней информационной полосы, текст слева и один портрет справа в главном слайдере, ровные сетки товаров, подборки, категории, живые примерки и светлый подвал. Это реализация по указанному референсу; её окончательное одобрение пользователем не заявлено. Прежний диптих, публичный Oswald, латунные блоки и тёмный подвал больше не определяют систему.

Документ фиксирует фактические `static/css/site.css`, `templates/base.html`, `templates/boutique/home.html` и `static/js/site.js`. Исполняемые токены принадлежат CSS; frontmatter — их синхронизируемый снимок. Отдельный адаптер `static/css/admin.css` сохраняет собственную рабочую тему. Sidecar содержит расширения и примеры; синтетические OKLCH-полосы показывают палитру, но не являются новыми CSS-токенами. Здесь не заявлены утверждённый image-comp или полное прохождение comp-led процесса.

**Key Characteristics:**
- Белые и светло-серые поверхности, чёрные действия, редкий светло-зелёный акцент.
- Golos на всём публичном сайте, умеренные заголовки и понятная магазинная иерархия.
- Ровная сетка четыре/две колонки и мягкие углы карточек и контролов.
- Ручной слайдер с портретом, стрелками и точками; реальные видео с явным Play.

## Colors

Основная палитра нейтральная, со светлым зелёным акцентом. Точные значения находятся в frontmatter.

### Primary

- **Ink** — текст и фон основных действий.
- **Dark** — чёрная информационная полоса и фон видео, не фон подвала.
- **Accent** — светлый зелёный: выделение текста, бейджи наличия и hover отдельных контролов.
- **Button hover** — тёмный серо-зелёный фон основной кнопки.

### Neutral

- **Paper** — белый фон страниц, шапки, полей и карточек бутиков.
- **Surface** — светло-серый фон фильтров, вкладок, размеров и подвала.
- **Hero** — тёплый нейтральный фон главного слайдера.
- **Muted** — вторичный текст и метаданные.
- **Atelier** — светлая плоскость производства.
- **Field border / Divider** — тонкие границы полей и разделителей.
- **Scrollbar thumb** — видимый серый ползунок на Surface.

Admin-токены принадлежат отдельному адаптеру: коричневая Primary, тёмная шапка, бронзовые ссылки и hover, светлая выбранная строка и собственные scrollbar-цвета. Публичный Accent и локальный admin `--accent` имеют разные роли. Их нельзя смешивать.

## Typography

Публичный сайт использует локальный variable **Golos** (400–900), fallback Arial / sans-serif. Display и body ссылаются на одну семью. Заголовки средней насыщенности и отрицательный tracking создают магазинную иерархию без узкого редакционного шрифта.

- **Display** — видимый h2 слайдера, максимум 11ch. До 1150 px размер 58 px, до 900 px — 46 px; до 600 px `clamp(22px,6.1vw,34px)`, line-height 1.12 и tracking -.035em. H1 главной присутствует как доступный скрытый заголовок.
- **Page title / Headline** — размеры из frontmatter. На телефоне основной заголовок страницы 38 px, заголовки секций 29 px. Заголовок карточки вещи — 15 px, на телефоне 13 px.
- **Body / Label** — основной текст 16 px, вспомогательный обычно 13–15 px; цены 15 px с весом 500.
- **Button** — 14 px и вес 500; внутри мобильной обложки 12 px.
- **Логотип** — Golos 34 px / 600, tracking -1.8 px, компактное LOOK 11 px. На телефоне логотип 28 px. Огромной wordmark в подвале нет.
- **Admin** — Golos 14 px / 1.5, заголовок формы 24 px. Oswald 32 px остаётся только в названии admin; его fallback Georgia/serif — существующее локальное расхождение, не правило публичного сайта.

## Layout

Контейнер имеет max-width 1440 px. Gutter адаптивный, до 900 px — 28 px, до 600 px — 20 px. Вертикальный Section: 80 / 64 / 52 px. Breakpoints — 1150, 900 и 600 px.

Информационная полоса 38 px, на телефоне 30 px; её средний текст скрывается до 900 px, правая ссылка — до 600 px. Белая шапка 84 / 74 / 66 px; desktop-навигация сменяется мобильной до 900 px.

Слайдер: текст слева, крупный силуэт без фотографического фона справа. Desktop-сетка 1fr/1fr с зазором 3%; высота сцены 660 px, до 900 px — 560 px, на телефоне — 460 px. Фотография — прозрачный PNG, пропорции сохраняются, низ силуэта обрезается краем сцены. Размер и смещение настроены для трёх текущих поз; на телефоне сетка 54% / 46%, текст выше изображения по слою. Точки и стрелки внизу по центру. Нет закрепления hero и второго кадра.

Товары и категории: ровные четыре колонки, до 900 px две; карточки без декоративных вертикальных смещений. Товарные фото 3:4; категории 3:4, на промежуточной ширине 4:5. Подборки показаны как группа ссылок-вкладок. На телефоне эта группа становится сеткой 2×N.

Примерки: три колонки с максимумом 1080 px; на телефоне горизонтальная scroll-snap лента с карточкой 76% ширины. Производство — две колонки и ограниченное по ширине вертикальное медиа; на телефоне текст над медиа. Бутики: две колонки, на телефоне одна. Светлый подвал: четыре смысловые колонки, затем три и две; бренд и Telegram-блок на телефоне занимают всю ширину.

Деталь товара: две равные колонки, sticky-галерея top 24 px только на desktop; до 600 px она статична над описанием. Фильтры меняются с пяти колонок на три, затем на две.

## Elevation & Depth

Основные поверхности плоские. Тени ограничены двумя функциональными состояниями: выбранная вкладка (`0 2px 7px #0000000d`) и выпадающее мобильное меню (`0 12px 30px #0002`). Карточки не получают декоративных теней. Глубину формируют реальные фотографии, мягкие фоны и светлые кнопки поверх изображений.

## Shapes

Control — скругления кнопок, полей, размеров и бейджей; Card — фотографии товаров, видео, галереи и адресные карточки; Category — категории. Точные значения в frontmatter. На телефоне фото товаров имеют 7 px, категории и видеокарточки 8 px. Desktop-вкладки округлые (24 px внутри контейнера 28 px), мобильные вкладки 5 px внутри панели 8 px. Стрелки слайдера круглые, точки диаметром 6 px. Публичный focus — outline 2 px и offset 5 px; admin offset 3 px.

## Components

### Buttons, navigation and icons

Основная кнопка Ink/Paper, минимальная высота 52 px, padding из frontmatter; hover — Button hover с белым текстом для всех вариантов, active сдвигает на 1 px. Light и secondary используют светлые фоны. Disabled снижает opacity до .35.

Desktop-навигация — ссылки 14 px с высотой от 44 px и underline для hover/current. Mobile — native details/summary; Escape закрывает меню и возвращает фокус, click снаружи закрывает меню. Пункты меню 48 px. Иконки — inline SVG, обычно 22 px со stroke 1.5, в кнопках 18 px. Запрет SVG-загрузок в CMS не распространяется на доверенные интерфейсные SVG.

### Campaign slider

Три текущие истории; предыдущая/следующая стрелка, точки, клавиши ←/→ внутри навигации и горизонтальный жест переключают вручную по кругу. Touch-action pan-y pinch-zoom сохраняет вертикальную прокрутку и масштабирование. Точки имеют aria-pressed; неактивные истории inert и aria-hidden, смена объявляется через aria-live. Контролы скрываются при одной истории. Без JS все истории доступны последовательно.

Смена: текст появляется с opacity и translateY 22 px за 650 мс; фотография — с opacity и мягким clip-path за 700 мс. Используется общая Ease из sidecar. Reduced motion выключает анимации и переходы. Нет autoplay, hero-video, sticky-scene или старой анимации диптиха.

### Collection links and catalog cards

Вкладки подборок — обычные ссылки с `?collection=…#selection`, а не обещание ARIA tablist. Активная ссылка получает aria-current, связанная панель видна. JS переключает панели без перезагрузки и синхронизирует history/popstate; без JS остаётся серверный маршрут.

Карточка вещи: фото, имя, цена отдельной строкой и метаданные. Статус — светло-зелёный бейдж; видео — белый бейдж с SVG Play. Белое действие внутри фото появляется на hover/focus-within, скрыто на телефоне до 600 px. Изображение слегка увеличивается до 1.025 за 500 мс. Сильные crop-top/bottom/waist масштабы удалены из действующего CSS; прежние `card_focus`-классы не задают визуальный стандарт.

Категории — фотографии с белым скруглённым названием-ссылкой внизу. Увеличение hover такое же, как у товаров. Пустые изображения и подборки имеют реальные текстовые состояния без выдуманного ассортимента.

### Media and provenance

Исходные Telegram-фотографии обычно 450×800. Они сохранены в lossless WebP без дополнительной потери при конвертации; это не повышает детализацию исходного JPEG. Карточки используют обычный cover, галереи — contain. В detail-галерее editorial-фото ограничены 450×800, постеры видео — шириной 720 px. По отдельному запросу пользователя для хиро добавлены три производные PNG с прозрачностью, обработанные встроенным Imagegen. Это AI-редактура, а не пиксельно идентичные исходники; исходные фото вещей не заменены. Источники и краткие промпты — `content/hero-cutouts.json`, общий реестр — `content/media.json`.

Видео сохранены как MP4 remux оригинальных потоков 720×1280 без повторного сжатия. Это исходное разрешение, не 4K. Native controls, playsinline, preload=none и явное Play действуют в примерках, производстве и галереях. JS останавливает видео вне видимости, при скрытии вкладки, смене галерейного слайда или запуске другого видео. Галерея объединяет фото и ролики в scroll-snap ленту со стрелками, счётчиком и переходом к видео; без JS остаются прокрутка и native controls.

### Fields, sizes and admin

Фильтры размещены на Surface со скруглением Card; белые поля с тонкой границей Field border имеют высоту 48 px и скругление Control. Label 13 px, ввод 14 px; на телефоне ввод 16 px. GET-форма сохраняет условия в URL.

Размер или объём — кнопки не ниже 48 px с фоном Surface; selected инвертируется в Ink/Paper. Заказ уходит в Telegram как черновик, отправку выполняет посетитель. Стандартная Django admin сохраняет отдельную коричнево-тёмную тему, штатные ошибки, полномочия и подтверждения; она не копирует публичный рекламный слайдер.

## Do's and Don'ts

### Do:
- **Do** опираться на пользовательский референс Anvogue и действующий код, сохраняя собственный ассортимент Colibri.
- **Do** использовать Golos для всех публичных заголовков, текста и управления.
- **Do** сохранять ровную сетку и заданные скругления карточек, полей и кнопок.
- **Do** использовать исходные фото и видео с происхождением в `content/media.json`; соблюдать ограничения их разрешения.
- **Do** сохранять доступный focus, reduced motion, нативное видео и серверные переходы без JS.
- **Do** синхронизировать frontmatter, sidecar и CSS при изменениях системы.

### Don't:
- **Don't** возвращать прежний диптих, публичный Oswald, латунную тему или тёмный подвал как действующий стандарт.
- **Don't** заявлять одобрение готового сайта, которого пользователь ещё не дал.
- **Don't** выдавать lossless-конвертацию или remux за восстановление деталей, повышение разрешения или 4K.
- **Don't** применять прежние сильные CSS-кропы к фотографиям товаров.
- **Don't** переносить скидки, обещания доставки, корзину или отзывы из демо без подтверждения продуктом.
- **Don't** добавлять автосмену историй, автозапуск видео или перехват вертикальной прокрутки.


Верхняя чёрная информационная полоса удалена по запросу пользователя. Якорь `#top` находится на основной шапке. В нижней строке футера — «Разработано kozarezov.tech» со ссылкой https://kozarezov.tech (новая вкладка, noopener noreferrer).
