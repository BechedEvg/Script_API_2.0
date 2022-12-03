# Script_API_2.0
The script receives 2 arguments specified in quotes:
1. URL of the checked page.
2. **desktop user** agent for checking indexing (optional).

An example of running a script:
>  python3 main.py "https://avtology.com/cars"

Run script with user agent:
>  python3 main.py "https://avtology.com/cars" "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/62.0 "

The output of the script is three files:
1. result_check_google.json
2. result_check_page.json
3. result_analysis.json
