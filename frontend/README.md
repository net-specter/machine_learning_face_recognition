# Face Recognition With Machine learning

This project is a **Next.js + Tailwind CSS v4** setup with Node 22 compatibility, using the new Tailwind v4 features (`@theme inline`) for custom variables and theming.

---

## 🚀 Getting Started

### 1. Clone the Project

```bash
git clone <your-repo-url>
cd <your-project-folder>/frontend
```

### 2. Install Dependencies

```bash
npm install
```

> ⚠ **Note:** Node 22 is supported, but the Tailwind CLI is not needed. PostCSS handles compilation automatically.

### 3. Start Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 📂 Folder Structure

```
src/
├─ app/                      # Next.js App Router pages
│  ├─ globals.css            # Main Tailwind + theme CSS
│  ├─ layout.tsx             # Layout wrapper
│  └─ page.tsx               # Example page
├─ public/                   # Static assets (images, fonts)
├─ node_modules/             # Project dependencies
├─ postcss.config.mjs        # PostCSS config for Tailwind
├─ package.json
├─ package-lock.json
├─ next.config.ts
├─ tsconfig.json
└─ README.md
```

---

## 🎨 Customizing Tailwind Variables

Tailwind v4 supports **CSS variables** via `@theme inline`. You can easily create your own fonts, colors, and other variables.

### 1. Open `globals.css`

You will see a structure like this:

```css
@import "tailwindcss";

:root {
  --color-primary: #3b82f6; /* default primary color */
  --color-background: #ffffff;
  --color-foreground: #171717;
  --font-sans: Arial, Helvetica, sans-serif;
  --font-mono: monospace;
}

@theme inline {
  --color-primary: var(--color-primary);
  --color-background: var(--color-background);
  --color-foreground: var(--color-foreground);
  --font-sans: var(--font-sans);
  --font-mono: var(--font-mono);
}

body {
  background: var(--color-background);
  color: var(--color-foreground);
  font-family: var(--font-sans);
}
```

### 2. Customize Your Colors and Fonts

Simply change the CSS variable values under `:root`:

```css
:root {
  --color-primary: #6366f1; /* Indigo */
  --color-background: #f3f4f6; /* Gray-100 */
  --color-foreground: #111827; /* Gray-900 */
  --font-sans: "Inter", sans-serif;
  --font-mono: "Fira Code", monospace;
}
```

### 3. Use Variables in Your Components

Tailwind v4 automatically maps your variables to classes:

```html
<button class="bg-primary text-white px-4 py-2 rounded">Save</button>

<h1 class="text-primary font-sans text-3xl">Hello World</h1>
```

> ✅ `bg-primary` uses `--color-primary`  
> ✅ `text-primary` uses `--color-primary`  
> ✅ `font-sans` uses `--font-sans`

---

## 📌 Notes

- Tailwind CLI (`npx tailwindcss init`) is **not required** for Node 22 + v4.
- PostCSS handles compiling Tailwind automatically.
- For light/dark mode, just add media queries in `globals.css` as you like:

```css
@media (prefers-color-scheme: dark) {
  :root {
    --color-background: #0a0a0a;
    --color-foreground: #ededed;
  }
}
```

---

## ✅ Summary

1. Clone → Install → Run dev server
2. Tailwind v4 with Node 22 works via PostCSS
3. Customize variables in `globals.css` under `:root`
4. Optional `tailwind.config.mjs` to extend Tailwind features

---
