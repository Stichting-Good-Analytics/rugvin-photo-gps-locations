import os
import pandas as pd
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import datetime


def count_files_and_list_all_contents(folder_path):
    image_extensions = ['.JPG', '.jpg', '.jpeg', '.png', '.gif',
                        '.bmp', '.tiff', '.webp']  # Add or remove extensions as needed
    result = {}
    for root, _, files in os.walk(folder_path):
        image_files = [file for file in files if any(
            file.lower().endswith(ext) for ext in image_extensions)]
        # Calculate relative path to use as key
        relative_path = os.path.relpath(root, folder_path)
        # Use '.' to represent the root directory itself
        if relative_path == '.':
            relative_path = 'root'
        # Count files and list them under the current directory's key
        result[relative_path] = {'images_count': len(image_files), 'images': {file_name: None for file_name in image_files},
                                 'other_files_count': len(set(files)-set(image_files)), 'files': list(set(files)-set(image_files))}
    return result


def get_exif_data(image_path):
    """Load an image and return its EXIF data."""
    image = Image.open(image_path)
    exif_data = {}
    if hasattr(image, '_getexif'):
        exif_info = image._getexif()
        if exif_info is not None:
            for tag, value in exif_info.items():
                decoded = TAGS.get(tag, tag)
                if decoded == "GPSInfo":
                    gps_data = {}
                    for t in value:
                        sub_decoded = GPSTAGS.get(t, t)
                        gps_data[sub_decoded] = value[t]
                    exif_data[decoded] = gps_data
                else:
                    exif_data[decoded] = value
    return exif_data


def convert_to_degrees(value):
    """Convert GPS coordinates from DMS to degrees."""
    d, m, s = value
    return d + (m / 60.0) + (s / 3600.0)


def get_gps_location(image_path):
    """Extract GPS coordinates in degrees from an image's EXIF data."""
    exif_data = get_exif_data(image_path)
    gps_info = exif_data.get("GPSInfo", {})

    if gps_info:
        lat = gps_info.get("GPSLatitude")
        lat_ref = gps_info.get("GPSLatitudeRef")
        lon = gps_info.get("GPSLongitude")
        lon_ref = gps_info.get("GPSLongitudeRef")

        if lat and lon and lat_ref and lon_ref:
            lat = convert_to_degrees(lat)
            if lat_ref != "N":
                lat = -lat
            lon = convert_to_degrees(lon)
            if lon_ref != "E":
                lon = -lon
            return (lat, lon)
    return None


def get_image_date(image_path):
    """Extract the date when the image was taken."""
    exif_data = get_exif_data(image_path)
    datetime_str = exif_data.get("DateTimeOriginal")
    if datetime_str:
        try:
            datetime_obj = datetime.datetime.strptime(
                datetime_str, "%Y:%m:%d %H:%M:%S")
            return datetime_obj.date()  # Extract and return just the date part
        except ValueError:
            return None


def extract_image_metadata(image_path):
    gps_info = get_gps_location(image_path)
    date = get_image_date(image_path)
    return gps_info, date


def create_image_metadata_report(folder_path):

    results = count_files_and_list_all_contents(folder_path)

    # append metadata to dict
    for subdirectory in results.keys():
        subdirectory_dict = results[subdirectory]
        for image_name in subdirectory_dict['images'].keys():
            if subdirectory_dict['images_count'] != 0:
                file_path = os.path.join(folder_path, subdirectory, image_name)
                gps_info, date = extract_image_metadata(file_path)
                results[subdirectory]['images'] = {image_name: {
                    'gps_info': gps_info, 'date': date} for image_name in subdirectory_dict['images'].keys()}

    # flatten the images key into columns
    flattened_data = []
    for subfolder, details in results.items():
        for image_name, image_info in details['images'].items():
            flattened_data.append({
                'subfolder': subfolder,
                'image_name': image_name,
                'image_gps_info': image_info['gps_info'],
                'image_date': image_info['date'],
                'other_files_in_subfolder': results[subfolder]['files']
            })

    df = pd.DataFrame(flattened_data)
    df['parent_folder'] = folder_path
    df['image_path'] = df['parent_folder'] + \
        df['subfolder'] + '/' + df['image_name']
    df['folder_date'] = df['subfolder'].str.extract(r'(\d{4}-\d{2}-\d{2})')
    # substitute local path with NAS path
    df = df.replace(folder_path, 'volume1/photo', regex=True)
    # Initialize the accumulator column with empty strings
    df['viscode'] = ''

    # Regex pattern to match
    pattern = r'(L\d{3}R\d{3})'
    df['viscode_subfolder'] = df['subfolder'].str.extract(pattern)
    df['viscode_image_name'] = df['image_name'].str.extract(pattern)
    df['viscode_other_files'] = df['other_files_in_subfolder'].str.extract(
        pattern)
    df['viscode'] = df['viscxode_subfolder'].combine_first(
        df['viscode_image_name']).combine_first(df['viscode_other_files'])
    df.to_csv('../data/image_metadata_report.csv', sep=';')


if __name__ == "__main__":
    folder_path = '/Users/janinekhuc/PycharmProjects/rugvin-photo-gps-locations/data'
    create_image_metadata_report(folder_path)
