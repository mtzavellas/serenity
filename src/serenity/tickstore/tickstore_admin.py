from pathlib import Path

import fire

from serenity.tickstore.tickstore import LocalTickstore


def tickstore_admin(action: str, db: str, staging_dir: str = '/mnt/raid/data/behemoth/db'):
    if action == 'reindex':
        tickstore = LocalTickstore(Path(f'{staging_dir}/{db}'), timestamp_column='time')
        tickstore.reindex()
        tickstore.close()
    else:
        raise Exception(f'Unknown action: {action}')


if __name__ == '__main__':
    fire.Fire(tickstore_admin)
