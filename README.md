# Modular Gear Pair Generator

![Modular Gear Pair Generator interface](IMG/application.png)

A Windows desktop application for generating parametric 3D-printable gears and compound/modular gear assemblies with real-time 3D preview and STL export.

The project supports several external and internal gear types, automatic geometry calculation, multiple bore styles, helical-angle calculation, and a two-section composite gear workflow in which upper and lower gear sections can be configured independently.

## Project Goal

The goal of the project is to provide a practical desktop tool for quickly creating custom gears for prototyping, mechanical design, robotics and 3D printing without having to model each gear manually in CAD.

The application is intended to cover both simple single gears and more complex compound parts built from two gear sections on one axis.

## Main Features

- Parametric gear generation.
- Single-gear and two-section composite gear modes.
- Real-time interactive 3D preview.
- STL export for 3D printing and CAD workflows.
- Automatic module calculation from tooth count and outside diameter.
- Helix-angle calculator based on lateral tooth offset and gear length.
- Configurable pressure angle and profile shift.
- Multiple bore / shaft-hole types.
- Dark desktop interface built with PySide6.
- PyVista-based 3D visualization.
- Trimesh/NumPy geometry fallback when CadQuery is unavailable.

## Supported Gear Types

- **Spur gear** — external straight teeth.
- **Helical gear** — external angled teeth.
- **Double helical / herringbone gear**.
- **Internal spur gear**.
- **Internal helical gear**.
- **Internal double helical gear**.

Reference previews for the supported gear types are included in `assets/gear_types/`.

## Compound / Modular Gear Mode

One of the main features of the application is the ability to create a single part consisting of **two gear sections** positioned on the same axis.

The upper and lower sections can be configured independently, which makes the program useful for compound transmissions and custom reduction mechanisms.

Depending on the selected configuration, each section can have its own:

- gear type;
- number of teeth;
- diameter;
- module;
- height / length;
- helix parameters;
- bore configuration.

The resulting geometry can be previewed as one assembly and exported as STL.

## Automatic Geometry Calculation

When automatic parameters are enabled, the program can calculate the module from the entered outside diameter and tooth count:

```text
module = outside_diameter / (teeth + 2)
```

Typical defaults include:

- pressure angle: **20°**;
- profile shift: **0**;
- helix angle: **0°** for spur gears;
- helix angle: **20°** for helical gears when not explicitly specified.

## Helix Angle Calculator

For helical gears, the application includes a helper for calculating the tooth angle from lateral offset and gear length:

```text
helix_angle = atan(helix_offset / gear_length)
```

The result is displayed in degrees and can be used directly in the gear parameters.

## Bore Types

Supported shaft-hole options include:

- no hole;
- circular bore;
- square bore;
- hexagonal bore;
- hollow/open center;
- keyway-style bore.

## Gear Profile Geometry

The gear profile implementation uses an involute-based tooth shape.

A key geometry fix in this version is the creation of a **single continuous closed gear outline** instead of unioning isolated tooth polygons. This prevents detached tooth fragments when the root circle lies inside the base circle, which is common on low-tooth-count gears.

The corrected profile:

- starts the involute at the valid base/root region;
- adds the required transition between the root circle and involute;
- joins neighboring teeth along the actual root circle;
- closes the full outline as one continuous contour;
- produces a watertight mesh for normal configurations.

## 3D Preview

The integrated preview allows you to inspect the generated geometry before exporting.

Typical controls:

- **Left mouse button** — rotate.
- **Mouse wheel** — zoom.
- **Middle mouse button / Shift + left mouse button** — pan.

## STL Export

Generated parts can be exported directly to STL for use in slicers or further CAD processing.

A typical generated filename follows the pattern:

```text
gear_[type]_[teeth]T_[module]M.stl
```

## Technology Stack

- **Python 3.11**
- **PySide6** — desktop GUI
- **PyVista / PyVistaQt** — interactive 3D preview
- **Trimesh** — mesh generation and export
- **NumPy** — numerical geometry calculations
- **CadQuery** — optional geometry backend when available

## Project Structure

```text
Modular-Gear-Pair-Generator/
├── IMG/
│   └── application.png
├── assets/
│   └── gear_types/
├── core/
│   ├── composite_builder.py
│   ├── export.py
│   ├── gear_builder.py
│   ├── gear_math.py
│   ├── gear_profiles.py
│   ├── holes.py
│   └── print_optimize.py
├── gui/
│   ├── dark_theme.py
│   ├── gear_type_preview.py
│   ├── hole_fields.py
│   ├── main_window.py
│   └── preview_widget.py
├── install.bat
├── start.bat
├── requirements.txt
└── main.py
```

## Installation

On Windows, run:

```text
install.bat
```

The installer prepares the dependencies required by the application.

Then start the program with:

```text
start.bat
```

Alternatively, with an existing Python environment:

```bash
pip install -r requirements.txt
python main.py
```

## Use Cases

- Custom gears for 3D printing.
- Compound gearboxes and reduction mechanisms.
- Robotics prototypes.
- Mechanical experiments.
- Replacement gears for non-critical mechanisms.
- CAD concept development.
- Rapid testing of tooth count, module and bore configurations.

## Version

This repository contains the **first public version** of the generator. The project architecture is intended to allow additional gear-generation modes and geometry improvements in future versions.

## Notes

For load-bearing or safety-critical mechanisms, generated gears should be independently checked for material strength, tolerances, backlash and manufacturing accuracy before use.
