from src.date_helper import DateConverter
from src.download_pictures import PictureDownloader
from src.exceptions import InvalidInput
from src.homepage_handler import HomePageHandler
from src.search_page_handler import SearchPageHandler
from RPA.Browser.Selenium import Selenium
from robocorp.tasks import task
from src.excel_report import ExcelReport
from robocorp import workitems
from RPA.Robocorp.WorkItems import WorkItems


browser_lib = Selenium()


def validate_inputs(**inputs):
    if not inputs.get("searchPhrase"):
        raise InvalidInput("searchPhrase is required")
    if inputs.get("numberOfMonths") < 0:
        raise InvalidInput("numberOfMonths must be greater than or equal to 0")


@task
def extract_nytimes_news():
    try:
        payload = workitems.inputs.current.payload
        SEARCH_PHRASE = payload.get("searchPhrase")
        CATEGORIES = payload.get("categories", [])
        NUMBER_OF_MONTHS = payload.get("numberOfMonths", 0)
        validate_inputs(searchPhrase=SEARCH_PHRASE,
                        numberOfMonths=NUMBER_OF_MONTHS)

        HomePageHandler(browser_lib).search(SEARCH_PHRASE)

        search_page_handler = SearchPageHandler(browser_lib)
        search_page_handler.accept_cookies()
        search_page_handler.sort_by_newest()
        search_page_handler.select_categories(CATEGORIES)

        end_date = DateConverter.get_end_date_from_months(NUMBER_OF_MONTHS)
        news = search_page_handler.get_news_until(end_date)
        work_items = WorkItems()
        work_items.get_input_work_item()
        out = work_items.create_output_work_item({
            "news": [n.to_dict() for n in news],
            "searchPhrase": SEARCH_PHRASE
        })
        out.save()
        work_items.set_current_work_item(out)
        browser_lib.close_all_browsers()

    except InvalidInput as e:
        raise e

    except Exception as e:
        raise e


@task
def download_news_pictures():
    payload = WorkItems().get_current_work_item().payload
    PictureDownloader.download(payload["news"])


@task
def generate_excel_report():
    payload = WorkItems().get_current_work_item().payload
    ExcelReport.generate(payload["news"], payload["searchPhrase"])
