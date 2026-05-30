# Cursores Personalizados Ábacos

Este proyecto incluye un set de cursores personalizados para la aplicación documental de Ábacos. Están inspirados en el logo local del proyecto, especialmente en la A central, las cuentas del ábaco y la paleta rojo, azul, verde y amarillo.

Los cursores están diseñados con contornos finos para que aporten identidad sin ocupar demasiado peso visual. La aplicación incluye además un rastro sutil de cuentas de colores cuando se mueve el cursor normal, inspirado en las cuentas del ábaco.

## Cursores Creados

- `abacos-cursor-default.svg` / `.png`: cursor normal.
- `abacos-cursor-pointer.svg` / `.png`: botones, enlaces y elementos clicables.
- `abacos-cursor-text.svg` / `.png`: campos de texto y edición.
- `abacos-cursor-help.svg` / `.png`: ayuda, información y tooltips.
- `abacos-cursor-wait.svg` / `.png`: estados de espera o carga.
- `abacos-cursor-not-allowed.svg` / `.png`: elementos deshabilitados.
- `abacos-cursor-grab.svg` / `.png`: elementos arrastrables.
- `abacos-cursor-grabbing.svg` / `.png`: elemento durante arrastre.

## Ubicación

Los assets están en:

```text
apps/web/public/cursors/
```

En Next.js, todo lo que vive en `public` se sirve desde la raíz del sitio. Por eso las reglas CSS usan rutas como:

```css
url("/cursors/abacos-cursor-default.svg")
```

Estas rutas no dependen del usuario de Windows y funcionan en navegador, Vercel y empaquetados tipo Electron siempre que se conserve el directorio público.

## CSS Modificado

El archivo global modificado es:

```text
apps/web/src/app/globals.css
```

Se añadieron reglas para:

- `html, body`
- `.cursor-default`
- `a`, `button`, `[role="button"]`, `.clickable`, `.cursor-pointer`
- `input`, `textarea`, `[contenteditable="true"]`, `.cursor-text`
- `.help`, `.info`, `[data-help]`, `[data-tooltip]`, `[title]`, `.cursor-help`
- `.loading`, `.is-loading`, `[aria-busy="true"]`, `.cursor-wait`
- `.draggable`, `[draggable="true"]`, `.cursor-grab`
- `.dragging`, `.draggable:active`, `[draggable="true"]:active`, `.cursor-grabbing`
- `button:disabled`, `[disabled]`, `.disabled`, `[aria-disabled="true"]`, `.cursor-not-allowed`

Cada regla tiene fallback:

```css
cursor:
  url("/cursors/abacos-cursor-default.svg") 4 4,
  url("/cursors/abacos-cursor-default.png") 4 4,
  auto;
```

## Efecto De Cuentas Al Mover El Cursor

La app monta el componente:

```text
apps/web/src/components/layout/CursorBeadTrail.tsx
```

Este componente crea cuentas de colores con brillo suave cuando se mueve el cursor normal. El efecto dibuja un rastro discreto, con cuentas de 6-9px que caen y se deshacen en torno a un segundo. Está limitado para no resultar invasivo:

- No aparece sobre enlaces, botones, inputs, elementos deshabilitados, carga o arrastre.
- No se ejecuta en dispositivos táctiles o con puntero grueso.
- Respeta `prefers-reduced-motion: reduce`.
- El número de cuentas vivas está limitado y desaparecen en torno a un segundo.

La página `cursor-preview.html` incluye el mismo efecto en versión estática para poder comprobarlo sin entrar en la app.

## Cambiar Un Cursor

Sustituye el SVG correspondiente en `apps/web/public/cursors/` manteniendo el mismo nombre. Si cambias mucho la silueta, revisa también el hotspot en `globals.css`.

## Ajustar Tamaño

Los SVG tienen `width="32"`, `height="32"` y `viewBox="0 0 32 32"`. Para otro tamaño:

1. Cambia `width` y `height` en el SVG.
2. Mantén un `viewBox` coherente.
3. Regenera el PNG de respaldo.
4. Revisa el hotspot.

No conviene superar 32x32 salvo para casos muy concretos: cursores grandes pueden resultar invasivos y menos accesibles.

## Ajustar Hotspot

El hotspot se define en CSS después del `url()`:

```css
cursor: url("/cursors/abacos-cursor-pointer.svg") 12 4, pointer;
```

Los dos números indican la coordenada activa dentro del cursor. Ejemplos actuales:

- Default: `4 4`
- Pointer: `12 4`
- Text: `16 16`
- Help: `16 16`
- Wait: `16 16`
- Not allowed: `16 16`
- Grab/grabbing: `16 16`

## Desactivar Temporalmente

Añade este atributo al elemento `html`:

```html
<html data-abacos-cursors="off">
```

La regla global:

```css
html[data-abacos-cursors="off"],
html[data-abacos-cursors="off"] * {
  cursor: auto !important;
}
```

permite desactivar el set para pruebas de accesibilidad o depuración.

## Añadir Nuevos Cursores

1. Crea el SVG en `apps/web/public/cursors/`.
2. Exporta PNG con el mismo nombre base.
3. Añade una regla en `apps/web/src/app/globals.css`.
4. Añade el caso a `apps/web/public/cursors/cursor-preview.html`.
5. Documenta el uso aquí.

## Previsualización

La página de prueba está en:

```text
apps/web/public/cursors/cursor-preview.html
```

Con el servidor local abierto, se puede visitar:

```text
http://127.0.0.1:3000/cursors/cursor-preview.html
```

## Accesibilidad

- Los cursores mantienen fallback nativo.
- Las siluetas son pequeñas y con contorno para verse sobre fondos claros y oscuros.
- No sustituyen estados visuales importantes como foco, hover, `disabled` o `aria-busy`.
- El set puede desactivarse con `data-abacos-cursors="off"`.
- No se recomienda usar cursores animados: pueden distraer y perjudicar a usuarios sensibles al movimiento.

## Limitaciones

- Algunos navegadores aplican límites internos al tamaño de cursores personalizados.
- SVG funciona en navegadores modernos; PNG queda como respaldo.
- En elementos con `pointer-events: none`, el cursor mostrado puede ser el del elemento inferior.
- En móviles y pantallas táctiles los cursores no se muestran.
