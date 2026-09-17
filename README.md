# Modular Gear Pair Generator

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

Depending on the selected configuration, each section can have its own gear type, tooth count, diameter, module, height, helix parameters and bore configuration. The resulting geometry can be previewed as one assembly and exported as STL.

## Automatic Geometry Calculation

When automatic parameters are enabled, the program can calculate the module from the entered outside diameter and tooth count:

```text
module = outside_diameter / (teeth + 2)
```

Typical defaults include a 20° pressure angle, zero profile shift, 0° helix for spur gears and a 20° default helix for helical gears when not explicitly specified.

## Helix Angle Calculator

For helical gears, the application includes a helper for calculating the tooth angle from lateral offset and gear length:

```text
helix_angle = atan(helix_offset / gear_length)
```

## Bore Types

Supported shaft-hole options include no hole, circular, square, hexagonal, hollow/open-center and keyway-style bores.

## Gear Profile Geometry

The gear profile implementation uses an involute-based tooth shape. A key geometry fix in this version is the creation of a **single continuous closed gear outline** instead of unioning isolated tooth polygons. This avoids detached tooth fragments when the root circle lies inside the base circle and helps produce watertight meshes for normal configurations.

## 3D Preview and STL Export

The integrated preview lets the user rotate, zoom and pan the generated geometry before export. Generated parts can be exported directly to STL for slicers or further CAD processing.

## Technology Stack

- **Python 3.11+**
- **PySide6** — desktop GUI
- **PyVista / PyVistaQt** — interactive 3D preview
- **Trimesh** — mesh generation and export
- **NumPy** — numerical geometry calculations
- **CadQuery** — optional geometry backend when available

## Project Structure

```text
Modular-Gear-Pair-Generator/
├── assets/gear_types/
├── core/
├── gui/
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

The installer creates a local `.venv`, upgrades `pip`, and installs dependencies from `requirements.txt`. Python 3.11+ must already be installed and available as `py` or `python`.

Then run:

```text
start.bat
```

Alternatively:

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

This repository contains the **first public version** of the generator and is structured for future gear-generation modes and geometry improvements.

## Notes

For load-bearing or safety-critical mechanisms, generated gears should be independently checked for material strength, tolerances, backlash and manufacturing accuracy before use.
