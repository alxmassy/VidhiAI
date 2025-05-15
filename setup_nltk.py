import nltk
import os # Make sure os is imported at the top

print("--- Setting up NLTK 'punkt' resource (v2 with PY3 check) ---")

# Define a specific download directory within the project's venv for NLTK data
venv_path = os.environ.get('VIRTUAL_ENV')
if not venv_path:
    print("ERROR: Virtual environment does not seem to be active.")
    print("Please activate the venv and re-run this script.")
    exit()

nltk_data_in_venv = os.path.join(venv_path, 'nltk_data')
print(f"Target NLTK data directory (within venv): {nltk_data_in_venv}")

if not os.path.exists(nltk_data_in_venv):
    os.makedirs(nltk_data_in_venv)
    print(f"Created directory: {nltk_data_in_venv}")

if nltk_data_in_venv not in nltk.data.path:
    nltk.data.path.append(nltk_data_in_venv)
print(f"NLTK search paths now include: {nltk.data.path}")

try:
    print(f"\nAttempting to download 'punkt' to: {nltk_data_in_venv}")
    nltk.download('punkt', download_dir=nltk_data_in_venv, quiet=False, raise_on_error=True)
    print("'punkt' download process completed successfully.")

    original_punkt_dir = os.path.join(nltk_data_in_venv, 'tokenizers', 'punkt')
    if os.path.exists(original_punkt_dir):
        print(f"\nContents of newly downloaded {original_punkt_dir}:")
        for item in sorted(os.listdir(original_punkt_dir)):
            print(f"  - {item}")

        key_files = ["english.pickle", "collocations.tab", "abbrev.tab", "ortho.pickle"]
        print("\nChecking for essential files directly in 'punkt' directory:")
        all_found_in_root = True
        for kf in key_files:
            if os.path.exists(os.path.join(original_punkt_dir, kf)):
                print(f"  FOUND in 'punkt' root: {kf}")
            else:
                print(f"  MISSING in 'punkt' root: {kf}")
                all_found_in_root = False
        if all_found_in_root:
            print("All essential 'punkt' files seem to be present in the 'punkt' root.")
        else:
            print("NOTE: Not all essential 'punkt' files were found in the 'punkt' root. Checking PY3 subdir.")

        # --- Check inside PY3 subdirectory ---
        py3_dir_path = os.path.join(original_punkt_dir, 'PY3')
        if os.path.exists(py3_dir_path):
            print(f"\nContents of PY3 directory ({py3_dir_path}):")
            for item in sorted(os.listdir(py3_dir_path)):
                print(f"  - {item}")
            print("\nChecking for essential files within PY3 directory:")
            all_found_in_py3 = True
            for kf in key_files:
                if os.path.exists(os.path.join(py3_dir_path, kf)):
                    print(f"  FOUND in PY3: {kf}")
                else:
                    print(f"  MISSING in PY3: {kf}")
                    all_found_in_py3 = False
            if all_found_in_py3:
                print("All essential files seem to be present within the PY3 subdirectory.")
            else:
                print("ERROR: Not all essential files were found even within the PY3 subdirectory.")
        else:
            print(f"\nPY3 directory not found at {py3_dir_path}")
            if not all_found_in_root: # If not in root and PY3 doesn't exist, then major issue
                 print("ERROR: Essential files not found in 'punkt' root, and PY3 directory doesn't exist.")

    else:
        print(f"ERROR: Directory '{original_punkt_dir}' was NOT created by the download.")

except Exception as e:
    print(f"ERROR during 'punkt' download or inspection: {e}")

print("\n--- NLTK 'punkt' setup finished ---")