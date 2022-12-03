from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium_stealth import stealth
from usp.tree  import sitemap_tree_for_homepage
import cloudscraper
import os
import sys
import re
import json
from time import sleep


class DriverChrome:

    def __init__(self):
        self.driver = None
        self.options = webdriver.ChromeOptions()
        #self.options.add_argument('headless')
        self.options.add_argument("start-maximized")
        self.options.add_argument('--disable-blink-features=AutomationControlled')
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option('useAutomationExtension', False)

    def open_browser(self):
        self.driver = webdriver.Chrome(options=self.options, service=Service(rf"{os.getcwd()}/chromedriver"))

        stealth(self.driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
                )

    def close_browser(self):
        self.driver.quit()


# getting main tags from HEAD
class ScrapingHead:

    def __init__(self, source_page):
        self.parser = BeautifulSoup(source_page, 'lxml')

    def get_title(self):
        try:
            title = self.parser.find("head").find("title").text
            return title
        except:
            return "not_found"

    def get_description(self):
        try:
            description = self.parser.find("head").find(attrs={"name": "description"}).get("content")
            return description
        except:
            pass
        try:
            description = self.parser.find("head").find(attrs={"property": "og:description"}).get("content")
            return description
        except:
            return "not_found"

    def get_tag_canonical(self):
        try:
            title = self.parser.find("head").find("link", {"rel": "canonical"}).get("href")
            return title
        except:
            return "not_found"


class JsonRW:

    def json_write(self, name, in_dict):
        with open(f'{name}.json', 'w') as outfile:
            json.dump(in_dict, outfile, indent=4, ensure_ascii=False)

    def json_read(self, name):
        with open(f'{name}.json', 'r') as infile:
            return json.load(infile)


class GetHtml:

    def __init__(self):
        self.browser = DriverChrome()

    def get_url(url):
        scraper = cloudscraper.create_scraper()
        try:
            return scraper.get(url)
        except:
            return "no_connection"

    def get_webdriver_html(self, url, user_agent="default"):
        if user_agent != "default":
            self.browser.options.add_argument(f"user-agent={user_agent}")
        self.browser.open_browser()
        self.browser.driver.get(url)
        html = self.browser.driver.page_source
        self.browser.close_browser()
        return html

    # get page html from mobile emulation
    def get_webdriver_mobile_html(self, url, user_agent="default"):
        if user_agent == "default":
            self.browser.options.add_argument(
                "user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) AppleWebKit/603.1.30 (KHTML, likeGecko) Version/10.0 Mobile/14E304 Safari/602.1")
        else:
            self.browser.options.add_argument(f"user-agent={user_agent}")
        mobileEmulation = {'deviceName': 'iPhone 8'}
        self.browser.options.add_experimental_option('mobileEmulation', mobileEmulation)
        self.browser.open_browser()
        self.browser.driver.get(url)
        html = self.browser.driver.page_source
        self.browser.close_browser()
        return html


class ParsingUrl:

    def __init__(self, url):
        self.url = url
        self.domain = self.url.split("/")[2]

    def get_main_url(self):
        return "/".join(self.url.split("/")[:3])

    def get_url_without_http(self):
        return "/".join(self.url.split("/")[2:])

    def get_path_url(self):
        return "/".join(self.url.split("/")[3:])

    def get_domain(self):
        return self.domain

    def comparison_domain(self, url):
        try:
            url = url.split('/')[2]
            domain =  self.domain
            if self.domain.split(".")[0].lower() == "www":
                domain = self.domain[4:]

            if url.split(".")[0].lower() == "www":
                url = url[4:]

            if domain == url:
                return True

            return False
        except:
            return False


class ScrapingPage:

    def __init__(self, source_page):
        self.source_page = source_page
        self.parser = BeautifulSoup(source_page, 'lxml')

    # get structure and content of H tags
    def get_teg_h(self):
        list_tag_h = self.parser.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        dict_tag = {"h1": {"count": 0, "list_source": []}, "list_tag": []}
        for tag in list_tag_h:
            h = str(tag).split()[0][1:3]

            if h == "h1":
                dict_tag["h1"]["count"] += 1
                dict_tag["h1"]["list_source"].append(str(tag))

            if h not in dict_tag["list_tag"]:
                dict_tag["list_tag"].append(h)

        if len(dict_tag["list_tag"]) != 0:
            return dict_tag
        else:
            return "not_found"

    # get list of img tags
    def check_alt_img(self):
        img = self.parser.find_all("img")
        dit_img = {"img_amount": 0, "list_atl": []}
        for i in img:
            dit_img["img_amount"] += 1
            try:
                dit_img["list_atl"].append(i["alt"])
            except:
                pass
        return dit_img

    # check for google code on page
    def check_cod_google(self):
        dict_google_cod = {"analytics(ua)": "not_found", "analytics(ga4)": "not_found"}
        script = str(self.parser.find_all('script', {"src": True}))
        if script.find("googletagmanager.com/gtag/js") != -1:
            dict_google_cod["analytics(ga4)"] = "found"

        if script.find("google-analytics.com/analytics.js") != -1:
            dict_google_cod["analytics(ua)"] = "found"
        return dict_google_cod

    # get list of external links
    def get_external_link(self, url):
        list_link = []
        for page_element in self.parser.find_all("a"):
            try:
                link = page_element["href"]
                if link.split("/")[0] == "https:" or link.split("/")[0] == "http:":
                    if not ParsingUrl(url).comparison_domain(link):
                        list_link.append(link)
            except:
                pass
        return list_link


class AnalysisPage:

    def __init__(self, result_check_google, result_check_page):
        self.result_check_google = result_check_google
        self.result_check_page = result_check_page

    def comparison_len(self, tag):
        if self.result_check_google["google_index_mobile"] == "yes":
            if self.result_check_page["page_content"][tag] != "not_found":
                len_tag_site = len(self.result_check_page["page_content"][tag])
                len_tag_google = len(self.result_check_google[tag])
                len_tag = len_tag_site - len_tag_google
                if len_tag > 0:
                    len_tag = f"site {tag} is {len_tag} more than google {tag}"
                elif len_tag < 0:
                    len_tag = f"google {tag} is {len_tag * -1} more than site {tag}"
                else:
                    len_tag = f"{tag}s are equal"
                result_title = {
                    f"len_{tag}_site": len_tag_site,
                    f"len_{tag}_google": len_tag_google,
                    "comparison": len_tag
                }
                return result_title

    def check_h_tag_structure(self):
            list_tag = self.result_check_page["page_content"]["list_tag"]["list_tag"]
            if len(list_tag) > 1 and sorted(list_tag) != list_tag:
                return "violated"
            return "not_violated"

    # check if the image has an "alt" and matches the title
    def check_img_alt(self):
        result = {"empty": "no", "duplicate": "no"}
        list_alt = self.result_check_page["page_content"]["images_alt"]["list_atl"]
        amount_img = self.result_check_page["page_content"]["images_alt"]["img_amount"]
        if len(list_alt) != amount_img:
            result["empty"] = "yes"
        if len(set(list_alt)) != amount_img:
            result["duplicate"] = "yes"
        return result

    def check_canonical(self, url):
        result = {"empty_canonical": "no", "compare_with_url": "equal"}
        if self.result_check_page["page_content"]["canonical"] == "not_found":
            result["empty_canonical"] = "yes"
        if self.result_check_page["page_content"]["canonical"] != url:
            result["compare_with_url"] = "not_equal"
        return result

    def check_external_link(self):
        result_list = []
        external_link = self.result_check_page["page_content"]["external_link"]
        for page in external_link:
            status_cod = GetHtml.get_url(page).status_code
            if status_cod != 200:
                result_list += page
        return result_list


class Sitemap:

    def __init__(self, url):
        self.url = ParsingUrl(url).get_main_url()

    def check_sitemap(self):
        sitemap = self.url + "/sitemap.xml"
        if GetHtml.get_url(sitemap).status_code == 200:
            return sitemap

        sitemap = self.url + "/robots.txt"
        if GetHtml.get_url(sitemap).status_code == 200:
            try:
                sitemap = GetHtml.get_url(sitemap).text.split("\n")
                for line in sitemap:
                    line = line.split()
                    if line[0].lower() == "sitemap:" and ParsingUrl(self.url).comparison_domain(line[1]):
                        return sitemap
            except:
                pass

        return "not_found"

    def get_url_list_in_sitemap(self):
        list_page = []
        for page in sitemap_tree_for_homepage(self.check_sitemap()).all_pages():
            if page.url not in list_page:
                list_page.append(page.url)
        return list_page


# check index pages in search
def check_index_pages(html, url, device="desktop"):
    parser = BeautifulSoup(html, "lxml")
    page_source = parser.find(class_="MjjYud")
    if page_source and device == "desktop":
        page_url = page_source.find(class_="yuRUbf").find("a")["href"]
        if page_url == url:
            return "yes"
    elif page_source and device == "mobile":
        page_url = page_source.find(class_="cz3goc BmP5tf")["href"]
        if page_url == url:
            return "yes"
    return "no"


def check_robots(url):
    robot_check = {"allow_url": "yes", "url_sitemap": "not_found"}
    url = ParsingUrl(url)
    url_path = "/" + url.get_path_url()
    patch_robot = url.get_main_url() + "/robots.txt"
    page_robot = GetHtml.get_url(patch_robot)

    if page_robot.status_code == 200:
        page_robot = page_robot.text.split("\n")
        for line in page_robot:
            try:
                line = line.split()
                if line[0].lower() == "sitemap:" and url.comparison_domain(line[1]):
                    robot_check["url_sitemap"] = "found"
            except:
                pass
        for line in page_robot:
            try:
                line = line.split()
                if line[0].lower() == "disallow:" and \
                        (line[1].lower() == url_path or line[1].lower() == url_path + "/"):
                    robot_check["allow_url"] = "no"
            except:
                pass

    return robot_check


def get_dict_google_check(url, user_agent_desktop):
    url_search = ParsingUrl(url).get_url_without_http()
    url_search = f"https://www.google.com/search?q=site:{url_search}"

    page_source_mobile = GetHtml().get_webdriver_mobile_html(url_search)
    check_index_mobile = check_index_pages(page_source_mobile, url, device="mobile")

    page_source_desktop = GetHtml().get_webdriver_html(url_search, user_agent_desktop)
    check_index_desktop = check_index_pages(page_source_desktop, url)

    dict_page = {"google_index_desktop": check_index_desktop, "google_index_mobile": check_index_mobile}

    if check_index_mobile == "yes":
        parser = BeautifulSoup(page_source_mobile, "lxml")
        url_source = parser.find(class_="MjjYud")
        title = url_source .find(class_="oewGkc LeUQr MUxGbd v0nnCb").text
        description = url_source .find(class_=re.compile("VwiC3b MUxGbd yDYNvb")).text.replace(u'\xa0', u' ')
        dict_page["google_index_mobile"] = check_index_mobile
        dict_page["title"] = title
        dict_page["description"] = description
        dict_page["len_title_mobile"] = len(title)
        dict_page["len_description_mobile"] = len(description)
        return dict_page
    return dict_page


def get_check_page_result_dict(base_status_code, url):
    robots = check_robots(url)
    sitemap = Sitemap(url)
    sitemap_url  = sitemap.check_sitemap()
    result_dict = {"status_code": base_status_code,
                   "robots": robots,
                   "check_url_in_sitemap": "no"
                   }
    if sitemap_url != "not_found":
        page_site_sitemap = sitemap.get_url_list_in_sitemap()
        if url in page_site_sitemap:
            result_dict["check_url_in_sitemap"] = "yes"
    else:
        pass
    if base_status_code == 200:
        page_source = GetHtml().get_webdriver_html(url)
        scraper_head = ScrapingHead(page_source)
        scraper_page = ScrapingPage(page_source)
        result_dict["page_content"] = {
            "title": scraper_head.get_title(),
            "description": scraper_head.get_description(),
            "canonical": scraper_head.get_tag_canonical(),
            "list_tag": scraper_page.get_teg_h(),
            "images_alt": scraper_page.check_alt_img(),
            "external_link": scraper_page.get_external_link(url),
            "google_cod": scraper_page.check_cod_google()
        }
    return result_dict


# site check main function
def check_page(url):
    base_status_code = GetHtml.get_url(url)
    if base_status_code != "no_connection":
        base_status_code = base_status_code.status_code
        result_dict = get_check_page_result_dict(base_status_code, url)
        return result_dict
    return "no_connection"


# get a dictionary with the parsed data
def get_result_analysis_dict(google_dict, check_site_dict, url):
    result_analysis_dict = {
        "google_index": {"index_desktop": google_dict["google_index_desktop"],
                         "index_mobile": google_dict["google_index_mobile"]},
        "status_code": check_site_dict["status_code"]
    }
    if check_site_dict["status_code"] == 200:
        analysis = AnalysisPage(google_dict, check_site_dict)
        result_analysis_dict["comparison_title"] = analysis.comparison_len("title")
        result_analysis_dict["comparison_description"] = analysis.comparison_len("description")
        result_analysis_dict["h1_count"] = check_site_dict["page_content"]["list_tag"]["h1"]["count"],
        result_analysis_dict["header_structure"] = analysis.check_h_tag_structure(),
        result_analysis_dict["images_alt"] = analysis.check_img_alt(),
        result_analysis_dict["canonical"] = analysis.check_canonical(url)
        result_analysis_dict["external_link"] = analysis.check_external_link()
    return result_analysis_dict


def main():
    url = sys.argv[1]
    user_agent_desktop = "default"
    if len(sys.argv) == 3:
        user_agent_desktop = " ".join(sys.argv[2:])
    result_check_google = get_dict_google_check(url, user_agent_desktop)
    result_check_page = check_page(url)
    result_analysis = get_result_analysis_dict(result_check_google, result_check_page, url)
    JsonRW().json_write("result_check_google", result_check_google)
    JsonRW().json_write("result_check_page", result_check_page)
    JsonRW().json_write("result_analysis", result_analysis)


if __name__ == "__main__":
    main()
