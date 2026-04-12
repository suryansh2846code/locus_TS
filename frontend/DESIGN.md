# The Design System: Digital Autonomy & Financial Sovereignty

## 1. Overview & Creative North Star
The Creative North Star for this system is **"The Kinetic Vault."** 

In a marketplace where autonomous AI agents handle complex financial transactions, the UI must feel like a high-security digital terminal that is simultaneously ethereal and grounded. We are moving away from the "flat web" into a layered, multi-dimensional space. By leveraging deep tonal depth and glassmorphism, we create an environment that feels expensive, secure, and cutting-edge. 

We avoid the "template" look by utilizing intentional asymmetry—placing high-density data tables against expansive, breathing hero sections—and employing a typography scale that favors dramatic contrast between technical headings and functional UI labels.

---

## 2. Color & Atmospheric Depth
Our palette is not just a set of swatches; it is an atmospheric map. The interplay between the deep `surface` (#0c0c21) and the neon accents creates a sense of high-energy data flowing through a dark void.

### The "No-Line" Rule
Prohibit the use of 1px solid, high-contrast borders for sectioning. Structural boundaries must be defined through **Background Tonal Shifts**. 
- To separate a sidebar from a main feed, transition from `surface` to `surface-container-low`. 
- To isolate a header, use a backdrop-blur with a semi-transparent `surface-bright` fill rather than a bottom stroke.

### Surface Hierarchy & Nesting
Treat the interface as a series of nested, translucent layers. Depth is achieved by "stacking" container tiers:
*   **Base Layer:** `surface` (#0c0c21) — The infinite canvas.
*   **Section Layer:** `surface-container-low` (#101129) — Used for large structural blocks.
*   **Interactive Layer:** `surface-container` (#161731) — Used for primary cards.
*   **Elevated Layer:** `surface-container-highest` (#222242) — Used for modals and floating pop-overs.

### Signature Textures & Glassmorphism
To achieve the "Kinetic Vault" aesthetic, use `surface-variant` at 40% opacity with a `20px` to `40px` backdrop-blur for floating elements. Main CTAs should never be flat; apply a subtle linear gradient from `primary` (#c799ff) to `primary-container` (#bc87fe) to give buttons "soul" and a tactile, glowing quality.

---

## 3. Typography
We utilize a dual-typeface system to balance technical precision with futuristic character.

*   **Headings (Space Grotesk):** This is our "Editorial" voice. Use `display-lg` and `headline-md` with tight letter-spacing (-0.02em) to convey authority. The geometric quirks of Space Grotesk reflect the autonomous, algorithmic nature of the marketplace.
*   **UI & Data (Inter):** Inter is our "Functional" voice. Used for `body-md`, `label-sm`, and data tables. It provides maximum legibility for financial figures (USDC/Locus) and agent status logs.

**Hierarchy Note:** Always pair a `display-sm` heading in Space Grotesk with a `label-md` in Inter (all caps, 0.05em tracking) to create a sophisticated, high-contrast header lockup.

---

## 4. Elevation & Depth
In this system, elevation is a product of light and transparency, not just shadows.

*   **The Layering Principle:** Place a `surface-container-lowest` card on a `surface-container-low` section. This creates a "recessed" or "carved" look that feels more integrated than a standard drop shadow.
*   **Ambient Shadows:** For floating modals, use an extra-diffused shadow: `0px 24px 48px rgba(0, 0, 0, 0.5)`. The shadow must feel like an absence of light rather than a grey smudge.
*   **The "Ghost Border":** When containment is required for accessibility, use a 1px stroke of `outline-variant` (#46465e) at **15% opacity**. This provides a "whisper" of a boundary that respects the glassmorphism aesthetic.
*   **Neon Glow:** Interactive states (Hover/Focus) should utilize a `primary` or `secondary` outer glow (4px - 12px blur) to simulate the emissive light of a futuristic terminal.

---

## 5. Components

### Buttons (The Glowing Pill)
*   **Primary:** Pill-shaped (`rounded-full`), `primary` background with a subtle glow. Text: `label-md` (Medium weight).
*   **Secondary:** Glass-pill. Semi-transparent `surface-variant` with a 15% `outline-variant` ghost border. 
*   **Tertiary:** No background. Text uses `secondary` (#4af8e3) with an underline that appears only on hover.

### Chips (Status Indicators)
*   Use `rounded-md` (1.5rem) for a sleek, modern look. 
*   **Active Agent:** `tertiary-container` fill with `on_tertiary_container` text and a 4px `tertiary` pulse dot.

### Glass Cards & Data Tables
*   **Cards:** Forbid divider lines. Use `surface-container-low` and vertical padding (from the spacing scale) to separate content.
*   **Data Tables:** Use `surface-container-lowest` for the header row and `surface` for the body. Separate rows with a 4px vertical gap instead of lines, allowing the background to peek through.

### Additional Marketplace Components
*   **Agent Pulse:** A custom component showing real-time activity using a `secondary` (#4af8e3) sparkline.
*   **Liquidity Gauge:** A horizontal bar using a gradient from `primary-dim` to `secondary-dim` to represent financial depth.

---

## 6. Do's and Don'ts

### Do:
*   **Do** use asymmetrical layouts. A 60/40 split is often more "premium" than a centered 50/50 split.
*   **Do** embrace negative space. The dark background is a luxury; let it breathe.
*   **Do** use `on-surface-variant` (#aaa8c5) for secondary text to maintain a soft visual hierarchy.

### Don't:
*   **Don't** use 100% white (#ffffff). Use `on-surface` (#e5e3ff) to keep the "navy" tint consistent across the UI.
*   **Don't** use standard "Material Design" shadows. They are too heavy for a glass-based system.
*   **Don't** use sharp corners. Our roundedness scale starts at `DEFAULT` (1rem); everything should feel approachable and engineered, not aggressive.
*   **Don't** ever use a solid 1px border to separate the navbar from the content. Use backdrop-blur and a tonal shift.