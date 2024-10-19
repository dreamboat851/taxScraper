# TaxScraper
A web app that scrapes taxonomy information from NCBI for scientific names of species provided by the user.


## TaxScraper Web App

This web app scrapes taxonomy information from the NCBI website when the user provides a list of scientific names of animals up to the species level in a text file. The program outputs all available taxonomy information from the NCBI website, and if it cannot obtain information for some species, it generates a separate file with those species names for the user to try manually.

### Usage Instructions

1. Upload a text file (`.txt`) or CSV file (`.csv`) with a list of scientific names (one name per line).
2. The app will scrape NCBI taxonomy information and generate:
   - A CSV file with the taxonomy information.
   - A text file with species names for which information could not be found.
3. Both files will be downloaded as a ZIP archive.

### Dependencies

This project requires the following Python libraries:
- beautifulsoup4
- Flask
- requests
- pandas
- numpy
- lxml
