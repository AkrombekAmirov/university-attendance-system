import subprocess
from database_file_path import get_file_path


def restore_postgres(backup_file):
    command = [
        'docker', 'exec', '-i', 'university_db',
        'psql', '-U', 'turnikeuser', '-d', 'turnikedb'
    ]
    with open(backup_file, 'r') as f:
        try:
            subprocess.run(command, stdin=f, check=True)
        except subprocess.CalledProcessError as e:
            print(f"{e.stderr.decode()}")


if __name__ == "__main__":
    restore_postgres(get_file_path('Database_2026-02-21_14-37-12.sql'))