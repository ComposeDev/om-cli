import os
import re
import logging
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def update_file_path(file_path, project_root, script_name, dry_run, change_counter):
    # Calculate the relative path from the project root
    relative_path = os.path.relpath(file_path, project_root)
    # Remove the project root directory from the relative path
    relative_path = relative_path.replace(f"{os.path.basename(project_root)}/", "", 1)
    relative_path_comment = f"# {relative_path}\n"

    with open(file_path, "r") as file:
        lines = file.readlines()

    # Regular expression to match the relative path comment format
    path_comment_regex = re.compile(r"^# .+\.py\n$")

    # Check if the first line is a comment with a path
    if lines and path_comment_regex.match(lines[0]):
        old_path = lines[0].strip()
        lines[0] = relative_path_comment
        logger.info(f"Updated {old_path} -> {relative_path.strip()}")
        change_counter[0] += 1
    elif lines and lines[0].startswith("# "):
        original_comment = lines[0].strip()
        lines.insert(0, relative_path_comment)
        logger.info(
            f"Inserted {relative_path.strip()} into {relative_path} (original comment: {original_comment})"
        )
        change_counter[0] += 1
    else:
        lines.insert(0, relative_path_comment)
        logger.info(f"Inserted {relative_path.strip()} into {relative_path}")
        change_counter[0] += 1

    if not dry_run:
        with open(file_path, "w") as file:
            file.writelines(lines)


def update_all_files_in_directory(directory, script_name, dry_run):
    project_root = os.path.abspath(
        os.path.join(directory, "..")
    )  # Adjust to get the project root
    logger.info(f"Base path: {project_root}")
    if dry_run:
        logger.info("Performing a dry run. No files will be updated.")
    change_counter = [0]  # Use a list to allow modification within functions
    for root, dirs, files in os.walk(directory):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for file in files:
            if file.endswith(".py") and file != script_name:
                file_path = os.path.join(root, file)
                update_file_path(
                    file_path, project_root, script_name, dry_run, change_counter
                )
    if change_counter[0] == 0:
        logger.info("No changes were made.")
    else:
        logger.info(f"Total changes made: {change_counter[0]}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Update file path comments in Python files."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without updating files.",
    )
    args = parser.parse_args()

    script_directory = os.path.dirname(
        os.path.abspath(__file__)
    )  # Get the directory of the script
    script_name = os.path.basename(__file__)  # Get the name of the script itself
    update_all_files_in_directory(script_directory, script_name, args.dry_run)
