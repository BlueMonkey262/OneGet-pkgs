from pathlib import Path
import yaml
import subprocess
import sys
import os

devMode = True

if devMode == True:
    folder = Path("/home/eli/PycharmProjects/OneGet/pkgs")
    print("Set folder to: ", folder)
else:
    if getattr(sys, 'frozen', False):
        folder = Path(sys.executable).parent / "pkgs"
    else:
        folder = Path(__file__).parent / "pkgs"

if devMode == True:
    installed_folder = Path("/home/eli/PycharmProjects/OneGet/installedPackages")
else:
    if getattr(sys, 'frozen', False):
        installed_folder = Path(sys.executable).parent / "installedPackages"
    else:
        installed_folder = Path(__file__).parent / "installedPackages"


# Recursively find all yaml, yml and oneget files and map basename (lowercase) to full path
yaml_paths = list(folder.rglob("*.yaml")) + list(folder.rglob("*.oneget")) + list(folder.rglob("*.yml"))
yaml_map = {p.stem.lower(): p for p in yaml_paths}
yaml_basenames = list(yaml_map.keys())


def install(quick="0"):
    if quick != "0":
        pkg = quick
    else:
        pkg = input("Please type the package you wish to install: ")
    pkg_lower = pkg.lower()

    if pkg_lower not in yaml_map:
        print(f"Package '{pkg}' not found.")
        return

    file_path = yaml_map[pkg_lower]

    try:
        with open(file_path, "r") as file:
            data = yaml.safe_load(file)

        # Validate sources section
        if not isinstance(data.get("sources"), dict):
            raise ValueError(f"Package '{pkg}' is missing a valid 'sources' section.")

        install_dict = data["sources"]
        filtered_install = {
            k: (v if isinstance(v, str) and v.upper() != "NA" else "Not Available")
            for k, v in install_dict.items()
        }

        recommend = data.get("recommend", "None provided")
        description = data.get("description", "None provided")

        print("Install: ", pkg)
        print("Description: ", description,"\n")

        print("1. APT:", filtered_install.get('apt', 'Not available'))
        print("2. Flatpak:", filtered_install.get('flatpak', 'Not available'))
        print("3. Snap:", filtered_install.get('snap', 'Not available'))
        print("\nEnter c to cancel.\n")
        print("The package recommends:", recommend, "\n")

        howInstall = input("How do you wish to install: ").strip()

        if howInstall not in ["1", "2", "3", "c", ""]:
            raise ValueError("Invalid selection.")

        if howInstall == "1" or (howInstall == "" and recommend == "apt"):
            cmd = f"apt install {filtered_install.get('apt', '')} -y"
            method_str = "apt"
        elif howInstall == "2" or (howInstall == "" and recommend == "flatpak"):
            cmd = f"flatpak install {filtered_install.get('flatpak', '')}"
            method_str = "flatpak"
        elif howInstall == "3" or (howInstall == "" and recommend == "snap"):
            cmd = f"snap install {filtered_install.get('snap', '')}"
            method_str = "snap"
        elif howInstall == "c":
            print("Cancelled.")
            return

        # Run the install command
        subprocess.run(cmd, shell=True)

        # After successful install, save package data with 'installed' info
        data["installed"] = {"method": method_str}
        installed_folder.mkdir(exist_ok=True)
        installed_path = installed_folder / f"{pkg}.yaml"
        with open(installed_path, "w") as f:
            yaml.dump(data, f)

        print(f"Installed '{pkg}' via {method_str}.")

    except yaml.YAMLError as e:
        print(f"YAML error in '{pkg}.yaml':", e)
    except Exception as e:
        print(f"Error processing package '{pkg}':", e)


def remove(quick="0"):
    packages = [f.stem for f in installed_folder.glob("*.yaml")] + [f.stem for f in installed_folder.glob("*.oneget")]

    if not packages:
        print("No packages currently installed that oneget knows about.")
        return

    if quick == "0":
        choice = input("Enter name of package to uninstall: ")
    else:
        choice = quick

    if choice == "c":
        print("Cancelled.")
        sys.exit(0)

    pkg = choice.lower()
    if pkg not in [p.lower() for p in packages]:
        print(f"Package '{choice}' is not installed or unknown.")
        return

    # Find actual installed package yaml file (case insensitive)
    installed_path = None
    for f in list(installed_folder.glob("*.yaml")) + list(installed_folder.glob("*.oneget")):
        if f.stem.lower() == pkg:
            installed_path = f
            break

    if installed_path is None:
        print(f"Could not find installed package file for '{choice}'.")
        return

    with open(installed_path, "r") as f:
        data = yaml.safe_load(f)

    method = data.get("installed", {}).get("method", "").lower()
    sources = data.get("sources", {})

    if method == "apt":
        cmd = f"apt remove {sources.get('apt', '')} -y"
    elif method == "flatpak":
        cmd = f"flatpak uninstall {sources.get('flatpak', '')}"
    elif method == "snap":
        cmd = f"snap remove {sources.get('snap', '')}"
    else:
        print("Unknown install method. Cannot uninstall.")
        return

    # Run uninstall command
    subprocess.run(cmd, shell=True)

    # Delete the installed yaml file
    installed_path.unlink()
    print(f"Uninstalled '{choice}'.")


def firstRun():
    print("Hello! Welcome to oneget, the place to get all your packages!")
    print("To start, try 'oneget install', either naming a package or selecting from the list.")
    print("\nWe currently support: APT, Flatpak, and Snap.")
    print("\nIn most UIs, you can type 'c' to cancel.")
    print("\nPrograms are YAML files, containing data about how to install the program.")
    print("\nOpen this UI by providing no arguments, first run, or 'help' argument.")


if (not os.path.exists("firstRun.txt")) or (open("firstRun.txt").read().strip().lower() == "false"):
    firstRun()

with open("firstRun.txt", "w") as file:
    file.write("false")

if len(sys.argv) < 2:
    firstRun()
else:
    command = sys.argv[1].lower()
    if command == "install":
        if len(sys.argv) > 2:
            if sys.argv[2] == "dev":
                devMode = True
                install()
            else:
                install(sys.argv[2])
        else:
            install()
    elif command in ["remove", "uninstall"]:
        if len(sys.argv) > 2:
            remove(sys.argv[2])
        else:
            remove()
    elif command == "uplist":
        # TODO: implement update list feature
        pass
    elif command == "help":
        firstRun()
