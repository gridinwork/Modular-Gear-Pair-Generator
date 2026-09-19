# Modular Gear Pair Generator

A Windows desktop application for generating parametric 3D-printable gears and compound/modular gear assemblies with real-time 3D preview and STL export.

The project supports several external and internal gear types, automatic geometry calculation, multiple bore styles, helical-angle calculation, print-shrinkage compensation, and a two-section composite gear workflow in which upper and lower gear sections can be configured independently.

## Project Goal

The goal of the project is to provide a practical desktop tool for quickly creating custom gears for prototyping, mechanical design, robotics and 3D printing without having to model each gear manually in CAD.

The application covers both simple single gears and more complex compound parts built from two gear sections on one axis.

## Main Features

- Parametric gear generation
- Single-gear and two-section composite gear modes
- Real-time interactive 3D preview
- STL export for 3D printing and CAD workflows
- Automatic module calculation from tooth count and outside diameter
- Helix-angle calculator based on lateral tooth offset and gear length
- Configurable pressure angle and profile shift
- Multiple bore / shaft-hole types
- ABS and PETG shrinkage compensation presets
- Dark desktop interface built with PySide6
- PyVista-based 3D visualization
- Trimesh/NumPy geometry fallback when CadQuery is unavailable

## Supported Gear Types

- **Spur gear** — external straight teeth
- **Helical gear** — external angled teeth
- **Double helical / herringbone gear**
- **Internal spur gear**
- **Internal helical gear**
- **Internal double helical gear**

The GUI supports optional local reference images for gear types. Image assets and application screenshots are intentionally not included in this public source snapshot.

## Compound / Modular Gear Mode

One of the main features is the ability to create a single part consisting of **two gear sections** positioned on the same axis.

The upper and lower sections can be configured independently, making the program useful for compound transmissions and custom reduction mechanisms.

Depending on the selected configuration, each section can have its own:

- gear type;
- number of teeth;
- outside diameter;
- module;
- height / length;
- helix parameters;
- bore configuration.

The resulting geometry can be previewed as one assembly and exported as STL.

## Automatic Geometry Calculation

When automatic parameters are enabled, the program can calculate module from the entered outside diameter and tooth count:

```text
module = outside_diameter / (teeth + 2)
```

Typical defaults include:

- pressure angle: **20°**
- profile shift: **0**
- helix angle: **0°** for spur gears
- helix angle: **20°** for helical gears when not explicitly specified

## Helix Angle Calculator

For helical gears, the application includes a helper for calculating tooth angle from lateral offset and gear length:

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

The integrated preview allows the generated geometry to be inspected before export.

Typical controls:

- **Left mouse button** — rotate
- **Mouse wheel** — zoom
- **Middle mouse button / Shift + left mouse button** — pan

## STL Export and Print Compensation

Generated parts can be exported directly to STL.

The application provides:

- nominal-size export;
- ABS preset with **0.8%** shrinkage compensation;
- PETG preset with **0.5%** shrinkage compensation.

A typical generated filename follows the pattern:

```text
gear_[type]_[teeth]T_[module]M.stl
```

## Technology Stack

- **Python 3.11+**
- **PySide6** — desktop GUI
- **PyVista / PyVistaQt** — interactive 3D preview
- **Trimesh** — mesh generation and export
- **NumPy** — numerical geometry calculations
- **Shapely** — 2D profile and bore geometry
- **mapbox-earcut** — polygon triangulation backend used by Trimesh
- **CadQuery** — optional geometry backend when available

## Project Structure

```text
Modular-Gear-Pair-Generator/
├── core/
│   ├── __init__.py
│   ├── composite_builder.py
│   ├── export.py
│   ├── gear_builder.py
│   ├── gear_math.py
│   ├── gear_profiles.py
│   ├── holes.py
│   └── print_optimize.py
├── gui/
│   ├── __init__.py
│   ├── dark_theme.py
│   ├── gear_type_preview.py
│   ├── hole_fields.py
│   ├── main_window.py
│   └── preview_widget.py
├── .gitignore
├── install.bat
├── start.bat
├── requirements.txt
└── main.py
```

## Installation

Python 3.11 or newer is recommended.

On Windows run:

```text
install.bat
```

The script creates a local `.venv`, upgrades pip and installs the dependencies.

Then start the application with:

```text
start.bat
```

Manual setup is also possible:

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python main.py
```

CadQuery is optional at runtime because the project includes a Trimesh/NumPy fallback. The remaining packages in `requirements.txt`, including the triangulation backend, are required for normal mesh generation and preview.

## Use Cases

- Custom gears for 3D printing
- Compound gearboxes and reduction mechanisms
- Robotics prototypes
- Mechanical experiments
- Replacement gears for non-critical mechanisms
- CAD concept development
- Rapid testing of tooth count, module and bore configurations

## Version

This repository contains the **first public version** of the generator. The architecture is intended to allow additional gear-generation modes and geometry improvements in future versions.

## Repository Notes

The public repository intentionally excludes screenshots, local Python runtimes, virtual environments, generated STL files, build output and cache files. These are either visual-only assets or generated/local dependencies and are not needed in source control.

## Verification

The Python source files were syntax-checked before publication. Full GUI execution and package installation require a Windows/Python environment with the dependencies from `requirements.txt`.

## Disclaimer

For load-bearing or safety-critical mechanisms, generated gears should be independently checked for material strength, tolerances, backlash and manufacturing accuracy before use.
