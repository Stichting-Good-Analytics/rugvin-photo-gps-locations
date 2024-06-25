# rugvin-photo-gps-locations

This repository serves as a helpful tool for Rugvin, providing an organized overview of the folder structure and extracting metadata from images, if available.

Key features include:
- Generating an overview of photos with their corresponding dates and GPS coordinates, if available.
- Extracting the _viscode_ from either the folder name or image name, following the naming convention LxxxRxxx.
- Obtaining the _date_ from the folder name or image EXIF data in the format YYYY-MM-DD.
- Retrieving latitude and longitude information from the EXIF data in image files.
- Listing additional files within the folder structure, such as Encounter 1.txt or Encounter sheet 05-05-2022.pdf.

_Note:_ For code to run, the folder_path in utils.py has to be adjusted.
