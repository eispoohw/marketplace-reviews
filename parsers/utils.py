import time

from tqdm import tqdm


def scroll_page_generator(driver, scroll_pause_time):
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        # Wait to load page
        time.sleep(scroll_pause_time)
        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
        yield


def scroll_page(driver, scroll_pause_time=1):
    print('Scrolling page...')
    for _ in tqdm(scroll_page_generator(driver, scroll_pause_time)): pass
    print('Scrolling completed!\n')
