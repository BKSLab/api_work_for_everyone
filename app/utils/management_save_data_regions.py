import os
import csv


def read_csv_file_with_data_regions() -> dict | None:
    """Чтение данных о регионах из CSV и возврат результата в виде словаря."""
    filepath = os.path.join(
        'utils', 'data_region', 'information_about_regions.csv'
    )
    if not os.path.isfile(filepath):
        return None
    try:
        with open(filepath, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=';', skipinitialspace=True)
            rows = [
                {
                    key: value
                    for key, value in zip(
                        [
                            'region_code_tv',
                            'region_name',
                            'federal_district_code',
                            'region_code_hh',
                        ],
                        one_record,
                    )
                }
                for one_record in reader
            ]
            return rows
    except csv.Error as error:
        print(f'error (csv.Error): {error}')
        return None
    except FileNotFoundError as error:
        print(f'error (FileNotFoundError): {error}')
        return None
    except Exception as error:
        print(f'error (Exception): {error}')
        return None
