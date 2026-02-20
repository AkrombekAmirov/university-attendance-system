import subprocess
from datetime import datetime
from database_file_path import get_file_path


def backup_postgres():
    backup_file = get_file_path(f"Database_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.sql")
    command = [
        'docker', 'exec', 'university_db',
        'pg_dump', '-U', 'turnikeuser', 'turnikedb'
    ]
    with open(f'{backup_file}', 'w') as f:
        try:
            subprocess.run(command, stdout=f, stderr=subprocess.PIPE, check=True)
            print(f"Backup muvaffaqiyatli olindi: {backup_file}")
        except subprocess.CalledProcessError as e:
            print(f"Backup olishda xatolik: {e.stderr.decode()}")


if __name__ == "__main__":
    backup_postgres()