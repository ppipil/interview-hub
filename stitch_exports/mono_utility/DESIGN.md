# Design System Specification: The Architectural Minimalist

## 1. Overview & Creative North Star
The "Architectural Minimalist" is a design system built on the philosophy of **Functional Sophistication**. It moves away from the generic "SaaS template" by embracing a high-end, tool-like precision that values whitespace as a structural element rather than empty space. 

**The Creative North Star: "The Digital Blueprint."**
This system treats the UI as an intentional, layered environment. We break the "standard" look by utilizing a high-contrast typography scale (pairing the geometric precision of Manrope with the utility of Inter) and replacing traditional borders with **Tonal Sectioning**. The result is an interface that feels like a premium Swiss watch or a high-end architectural drawing—engineered, reliable, and deceptively simple.

---

## 2. Colors & Surface Logic
The palette is rooted in `primary` (#0F172A) for authority and `secondary` (#4B41E1) for a soft, electric energy.

### The "No-Line" Rule
**Explicit Instruction:** Traditional 1px solid borders are strictly prohibited for defining sections. Instead, boundaries are created through background shifts. 
- Use `surface_container_low` for the main canvas.
- Use `surface_container_lowest` (pure white) for card elements to create a natural "pop."
- Use `surface_container_high` for sidebar or utility panels to create recession.

### Surface Hierarchy & Nesting
Treat the UI as a series of physical layers. 
- **Base Layer:** `surface` (#F7F9FB)
- **Content Blocks:** `surface_container_lowest` (#FFFFFF)
- **Nested Controls:** `surface_container` (#ECEEF0)

### The "Glass & Gradient" Rule
To ensure the "tool-like" feel doesn't become "flat," apply a **Signature Texture** to main CTAs. Use a subtle linear gradient from `secondary` (#4B41E1) to `secondary_container` (#645EFB) at a 135-degree angle. For floating navigation or modals, use Glassmorphism: `surface_container_lowest` at 80% opacity with a `20px` backdrop-blur.

---

## 3. Typography
We use a dual-typeface system to balance editorial personality with functional clarity.

*   **Display & Headlines (Manrope):** Chosen for its modern, geometric construction. Use `display-lg` and `headline-md` with tight letter-spacing (-0.02em) to create an authoritative, "designed" feel.
*   **Body & Labels (Inter):** The workhorse. Inter provides maximum legibility for data-heavy sections. 

**Hierarchy Strategy:** 
- Use `title-lg` in `on_surface` for card headers.
- Use `label-md` in `on_surface_variant` (all caps, +0.05em tracking) for category tags to enhance the "utility" aesthetic.

---

## 4. Elevation & Depth
In this design system, depth is a function of light and layering, not artificial decoration.

*   **The Layering Principle:** Avoid shadows on standard cards. Place a `surface_container_lowest` card onto a `surface_container_low` background. This "Tonal Lift" is cleaner and more professional than a drop shadow.
*   **Ambient Shadows:** For elevated elements (modals, dropdowns), use a "Long-Soft" shadow: 
    *   `box-shadow: 0 12px 40px rgba(15, 23, 42, 0.06);` 
    *   The shadow is tinted with the `primary` color (#0F172A) to feel natural to the environment.
*   **The "Ghost Border" Fallback:** If accessibility requires a container boundary, use `outline_variant` at 15% opacity. It should be felt, not seen.
*   **Glassmorphism:** Apply to tooltips and floating menus to maintain a sense of space. Use `surface_container_lowest` with a 12px blur.

---

## 5. Components

### Buttons
*   **Primary:** Gradient (`secondary` to `secondary_container`), white text, `md` (0.375rem) corner radius. High-end feel.
*   **Secondary:** `surface_container_high` background with `on_surface` text. No border.
*   **Tertiary:** Ghost style. `on_surface_variant` text that shifts to `primary` on hover.

### Input Fields
*   **Structure:** `surface_container_lowest` background. 
*   **Focus State:** Instead of a thick border, use a 2px outer "glow" using `secondary` at 20% opacity and a `0.5px` border of `secondary`.
*   **Label:** Use `label-md` positioned strictly above the field, never floating inside.

### Cards & Lists
*   **Cardinal Rule:** No divider lines. Separate list items using 8px of vertical whitespace or a subtle background toggle between `surface_container_low` and `surface_container_lowest`.
*   **Padding:** Use "Generous Padding"—minimum 24px (`xl` spacing) for card internals to allow the typography to breathe.

### Chips (Badges)
*   **Style:** `surface_container` background with `on_primary_container` text. Use `full` (9999px) radius for a friendly, modern contrast against the angular cards.

### Contextual Action Bar (New Component)
A floating, glassmorphic bar at the bottom of the screen using `surface_container_highest` at 70% opacity. This acts as a "Command Center" for the solo developer's tool, keeping the main canvas clear.

---

## 6. Do's and Don'ts

### Do:
*   **Do** use `headline-lg` for empty states to make the "nothingness" feel intentional and editorial.
*   **Do** use `primary_container` (#131B2E) for dark-mode-like "Power Sections" (e.g., a header or sidebar) to provide tonal depth.
*   **Do** use the `xl` (0.75rem) radius for large containers and `md` (0.375rem) for smaller interactive elements like buttons.

### Don't:
*   **Don't** use pure black (#000000) for text. Always use `on_surface` (#191C1E) to keep the contrast high but sophisticated.
*   **Don't** use 1px borders to separate content. Use a 16px or 24px gap instead.
*   **Don't** use standard blue for links. Use the "Electric Indigo" `secondary` (#4B41E1) to signify interactivity.