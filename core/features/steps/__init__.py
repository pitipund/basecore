import re
from datetime import timedelta

from django.utils import timezone
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.keys import Keys

from his.core.tests import utils
from his.core.utils import ad_to_be

TIMEOUT_WAIT_TO_SEE_ELEMENT = 8  # secs
TIMEOUT_DOCUMENT_READY = 20  # secs


def transform_text(context, value):
    # special keys
    value = value.replace('[down]', Keys.ARROW_DOWN)
    value = value.replace('[left]', Keys.ARROW_LEFT)
    value = value.replace('[right]', Keys.ARROW_RIGHT)
    value = value.replace('[up]', Keys.ARROW_UP)
    value = value.replace('[enter]', '\n')
    value = value.replace('[today]', ad_to_be(timezone.now().date()))
    value = value.replace('[empty]', '')
    if '[yesterday]' in value:
        yesterday = (timezone.now() - timedelta(days=1)).date()
        value = value.replace('[yesterday]', ad_to_be(yesterday))
    return value


class ElementNotFoundException(Exception):
    pass


def escape_quote(val):
    return val.replace('"', '\"')


index_pattern = re.compile('(.+)\[(\d+)\]')


def doc_label_locator(doc_label):
    match = index_pattern.match(doc_label)
    if match:
        name, index = match.group(1), match.group(2)
    else:
        name = doc_label
        index = 0
    return 'getElementsByDocLabel("%s", true)[%s]' % (escape_quote(name), index)


def get_first_element_by_doc_label(context, doc_label):
    """return first element by doc label

    if multiple elements with same doc_label exists,
    you can specify doc_label as  label[0], label[1] to retrieve the correct item"""
    try:
        webelement = context.browser.driver.execute_script(
            'return %s.dom' % doc_label_locator(doc_label))
    except WebDriverException as e:
        if "Cannot read property 'dom' of undefined" in e.args[0]:
            raise ElementNotFoundException('Could not find "%s"' % doc_label)
        return None
    return context.browser.element_class(webelement, context.browser)


def get_elements_by_doc_label(context, doc_label):
    """Return iterator of elements matched by doc_label"""
    index = 0
    while index < 100:  # prevent infinity loop
        try:
            webelement = context.browser.driver.execute_script(
                'var items = getElementsByDocLabel("%s", true);'
                'return (%d < items.length ? items[%d].dom : "out_of_range");' % (
                    escape_quote(doc_label), index, index))
            if webelement == 'out_of_range':
                return
            index += 1
            yield context.browser.element_class(webelement, context.browser)
        except WebDriverException as e:
            if "Cannot read property 'dom' of undefined" in e.args[0]:
                raise ElementNotFoundException('Could not find "%s"' % doc_label)
            return


def wait_for_loading_finish(context):
    script = 'return (!("jQuery" in window) || $(".loader").filter(function(){ return this.offsetParent }).length == 0)'

    def all_loader_hidden():
        if context.browser.driver.execute_script(script):
            return True
    utils.wait_for(context, all_loader_hidden, 'Loader still exists', timeout=10)


def retry_click_after_loader_hidden(e, context, button):
    """Retry click the button again if loading screen block the button

    :return true if successfully retry click the button"""
    if 'dimmer' in e.args[0]:
        # loading screen found?
        wait_for_loading_finish(context)
    if 'item' in e.args[0]:
        # This is to handle case that ComboBox is directly above Button to click
        # and we are unable to click, so we need to wait until ComboBox's item hidden
        # Then we retry the click
        context.browser.is_element_not_present_by_css('.menu.transition.visible')
    # retry click once more
    try:
        button.click()
        return True
    except WebDriverException as e2:
        pass
    return False
