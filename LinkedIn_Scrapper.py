import json
import os
import numpy as np
from time import sleep
from parsel import Selector
from selenium import webdriver
from selenium.webdriver.common.keys import Keys


def extract_linkedin_profiles(**cfgs):
    """
    Outputs into a JSON file containing the information scrapped from LinkedIn
    profiles.

    **cfgs:

    cfgs['keywords']: Keywords for the LinkedIn profile search search query
    cfgs['num_profiles']: number of LinkedIn profiles to be scrapped
    cfgs['output_folder']: folder name for which JSON files are written

    """
    driver = webdriver.Chrome('/Users/jaredandrews/FMP/chromedriver')
    driver.get('https://www.linkedin.com/login?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin')

    username = driver.find_element_by_name("session_key")
    username.send_keys('XXX')
    sleep(0.5)

    password = driver.find_element_by_name('session_password')
    password.send_keys('XXX')
    sleep(0.5)

    sign_in_button = driver.find_element_by_class_name('btn__primary--large')
    sign_in_button.click()
    sleep(2)

    driver.get('https://www.google.com/')
    search_query = driver.find_element_by_name('q')

    search_string = 'site:linkedin.com/in AND ('

    for cfg in cfgs['keywords']:
        search_string +=  '"' + cfg + '" OR '

    search_string = search_string.rstrip('OR ') + ')'

    search_query.send_keys(search_string)
    search_query.send_keys(Keys.RETURN)
    sleep(0.5)

    urls = []

    num_pages = int(np.ceil(cfgs['num_profiles']/10))

    # Get num_pages number of LinkedIn profile urls
    for _ in range(num_pages):
        _urls = driver.find_elements_by_xpath('//*[@class = "r"]/a[@href]')
        urls.extend([url.get_attribute('href') for url in _urls])
        next_button = driver.find_element_by_xpath("//*[contains(local-name(), 'span') and contains(text(), 'Next')]")
        next_button.click()

    def scroll_down(driver):
        """A method for scrolling the page, forcing elements to load."""

        # Get scroll height.
        height = driver.execute_script("return document.body.scrollHeight")

        for h in range(1,height,1000):

            # Scroll down to the bottom.
            command = "window.scrollTo(0, " + str(h) + ");"
            driver.execute_script(command)

            # Wait to load the page.
            sleep(1)

    profiles_list = []

    for url in urls:

        driver.get(url)

        scroll_down(driver)

        #show pulications details if exists
        try:
            button = driver.find_element_by_xpath('//button[@aria-label = "Expand publications section"]')
            driver.execute_script("arguments[0].click();", button)
        except:
            pass

        # Click any 'see-more' buttton to load all elements
        try:
            for button in driver.find_elements_by_xpath('//button[contains(@class,"see-more")]'):
                    driver.execute_script("arguments[0].click();", button)
        except:
            pass

        # Click any 'show-more' buttton to load all elements
        try:
            for button in driver.find_elements_by_xpath('//button[contains(@class,"show-more")]'):
                    driver.execute_script("arguments[0].click();", button)
        except:
            pass

        # Click the 'show-more' buttton for Skills section to load all elements if exists
        try:
            button = driver.find_element_by_xpath('//button[@class = "pv-profile-section__card-action-bar pv-skills-section__additional-skills artdeco-container-card-action-bar artdeco-button artdeco-button--tertiary artdeco-button--3 artdeco-button--fluid"]')
            driver.execute_script("arguments[0].click();", button)
        except:
            pass

        # Click the 'show-more' buttton for About section to load all elements if exists
        try:
            button = driver.find_element_by_xpath('//a[@href = "#" and @class = "lt-line-clamp__more"]')
            driver.execute_script("arguments[0].click();", button)
        except:
            pass


        sel = Selector(text=driver.page_source)

        if sel.xpath('//div[@class = "profile-unavailable"]'):
            continue

        # Get name
        name = sel.xpath('//*[@class = "inline t-24 t-black t-normal break-words"]/text()').extract_first().split()
        name = ' '.join(name).strip()

        # Get location
        location = ' '.join(sel.xpath('//*[@class = "t-16 t-black t-normal inline-block"]/text()').extract_first().split()).strip()

        # Get headline
        headline = sel.xpath('//*[@class = "mt1 t-18 t-black t-normal"]/text()').extract_first().split()
        headline = ' '.join(headline).strip()

        # Get About section text
        about = sel.xpath('//p[contains(@class,"about__summary-text")]/span/text()')
        if about:
            about_text = ''
            for line in about:
                about_text += ' ' + line.extract().strip('\n').strip(' ')
            about_text = about_text.strip('...').strip()
        else:
            about_text = None


        # Get Experience section information if exists
        if sel.xpath('//section[@id = "experience-section"]'):
            experiences = sel.xpath('//li[@class = "pv-entity__position-group-pager pv-profile-section__list-item ember-view"]')
            experience_list = []
            for experience in experiences:
                job_title = experience.xpath('.//div[contains(@class, "pv-entity__summary-info pv-entity__summary-info--background-section")]//h3/text()').extract_first()
                # if job_title is not None, this is the job, then company format for experience cell
                if job_title:

                    company_info = experience.xpath('.//div[contains(@class, "pv-entity__summary-info pv-entity__summary-info--background-section")]//p/text()').extract()
                    company = company_info[1] if company_info else None

                    job_duration_info = experience.xpath('.//h4[@class = "pv-entity__date-range t-14 t-black--light t-normal"]//span/text()').extract()
                    job_duration = job_duration_info[1] if job_duration_info else None

                    job_location_info = experience.xpath('.//h4[@class = "pv-entity__location t-14 t-black--light t-normal block"]//span/text()').extract()
                    job_location = job_location_info[1] if job_location_info else None

                    job_description_info = experience.xpath('.//div[@class="pv-entity__extra-details ember-view"]/p/text()').extract()
                    cleaned_job_description = [x.strip() for x in job_description_info if x.strip()!='']
                    job_description = ' '.join(cleaned_job_description).strip() if cleaned_job_description else None

                    job_dict = {'Job Title':job_title,'Company':company,'Job Dates':job_duration,
                                'Job Location':job_location, 'Job Description': job_description}

                    experience_list.append(job_dict)

                # if job_title is None, this is the company_job format for experience cell
                else:

                    company = experience.xpath('.//h3[@class="t-16 t-black t-bold"]/span/text()').extract()[1]

                    jobs_at_company = experience.xpath('.//li[@class="pv-entity__position-group-role-item"]')

                    jobs_at_company_list = []

                    for job in jobs_at_company:

                        job_info_header = job.xpath('.//div[contains(@class, "pv-entity__summary-info-v2 pv-entity__summary-info--background-section pv-entity__summary-info-margin-top")]')

                        job_info = job_info_header.xpath('.//h3/span/text()').extract()
                        job_title = job_info[1] if job_info else None

                        job_duration_info = job_info_header.xpath('.//h4[@class = "pv-entity__date-range t-14 t-black--light t-normal"]/span/text()').extract()
                        job_duration = job_duration_info[1] if job_duration_info else None

                        job_location_info = job_info_header.xpath('.//h4[@class = "pv-entity__location t-14 t-black--light t-normal block"]/span/text()').extract()
                        job_location = job_location_info[1] if job_location_info else None

                        job_description_info = job.xpath('.//div[@class="pv-entity__extra-details ember-view"]/p/text()').extract()
                        cleaned_job_description = [x.strip() for x in job_description_info if x.strip()!='']
                        job_description = ' '.join(cleaned_job_description).strip() if cleaned_job_description else None

                        job_dict = {'Job Title':job_title,'Company':company,'Job Dates':job_duration,
                                'Job Location':job_location, 'Job Description': job_description}

                        experience_list.append(job_dict)

        else:
            experience_list = None

        # Get Education section information if exists
        if sel.xpath('//section[@id = "education-section"]'):

            educations = sel.xpath('//li[@class = "pv-profile-section__list-item pv-education-entity pv-profile-section__card-item ember-view"]')

            education_list = []

            for education in educations:

                school = education.xpath('.//h3/text()').extract_first()

                degree_name_info = education.xpath('.//p[@class="pv-entity__secondary-title pv-entity__degree-name t-14 t-black t-normal"]/span/text()').extract()
                degree_name  = degree_name_info[1] if degree_name_info else None

                field_of_study_info = education.xpath('.//p[@class="pv-entity__secondary-title pv-entity__fos t-14 t-black t-normal"]/span/text()').extract()
                field_of_study = field_of_study_info[1] if field_of_study_info else None

                education_date_info = education.xpath('.//div[@class="pv-entity__extra-details ember-view"]/p/text()').extract()
                cleaned_education_date_info = [x.strip() for x in education_date_info if x.strip()!='']
                education_description = '  '.join(cleaned_education_date_info).strip() if cleaned_education_date_info else None

                education_dict = {'Institution Name': school ,'Degree Name':degree_name, 'Field of Study':field_of_study,
                                 'Education Info': education_description}

                education_list.append(education_dict)

        else:
            education_list = None

        # Get Certifications section information if exists
        if sel.xpath('//section[@id = "certifications-section"]'):

            certifications = sel.xpath('//li[@class = "pv-profile-section__sortable-item pv-certification-entity ember-view"]')

            certification_list = []

            for certification in certifications:

                certification_name = certification.xpath('.//h3[@class = "t-16 t-bold"]/text()').extract_first()

                issuing_authority_info = certification.xpath('.//p[@class = "t-14"]/span/text()').extract()
                issuing_authority = issuing_authority_info[1] if issuing_authority_info else None

                certification_dict = {'Certification': certification_name, 'Issuing Authority': issuing_authority}

                certification_list.append(certification_dict)
        else:
            certification_list = None

        # Get Skills section information if exists
        skills_endorsements = sel.xpath('//section[@class ="pv-profile-section pv-skill-categories-section artdeco-container-card ember-view"]')
        if skills_endorsements:
            skills = skills_endorsements.xpath('//span[@class="pv-skill-category-entity__name-text t-16 t-black t-bold"]/text()').extract()
            cleaned_skills = [x.strip() for x in skills]
        else:
            cleaned_skills = None

        publications_section = sel.xpath('//section[contains(@class,"accomplishments") and contains(@class,"publications")]')

        if publications_section:

            publications = publications_section.xpath('.//ul[contains(@class,"accomplishments")]/li')

            publications_list = []

            for publication in publications:

                publication_title_info = publication.xpath('.//h4[@class = "pv-accomplishment-entity__title"]/text()').extract()
                publication_title = publication_title_info[1].strip() if publication_title_info else None

                publication_date_info = publication.xpath('.//span[@class = "pv-accomplishment-entity__date"]/text()').extract()
                publication_date = publication_date_info[1].strip() if publication_date_info else None

                publication_publisher_info = publication.xpath('.//span[@class = "pv-accomplishment-entity__publisher"]/text()').extract()
                publication_publisher = publication_publisher_info[1].strip() if publication_publisher_info else None

                publication_description_info = publication.xpath('.//p[@class = "pv-accomplishment-entity__description t-14"]/text()').extract()
                publication_description = publication_description_info[1].strip() if publication_description_info else None

                publication_dict = {'Publication Title': publication_title, 'Publication Date': publication_date,
                                   'Publication Publisher': publication_publisher, 'Publication Description': publication_description}

                publications_list.append(publication_dict)

        else:
            publications_list = None


        # Create dictionary for LinkedIn profile
        profile_dict = {'Name':name, 'Location':location,'Headline':headline, 'About':about_text,
                        'Experience':experience_list,'Education': education_list,
                        'Certification':certification_list, 'Publications':publications_list,
                        'Skills and Endorsements':cleaned_skills, 'URL' : url}

        profiles_list.append(profile_dict)

    driver.close()

    output_file = cfgs['output_file']

    # Write list of LinkedIn profile dictionaries to JSON
    with open(output_file, 'w') as f:
        json.dump(profiles_list , f)


if __name__ == "__main__":
    cfgs = json.load(open('LinkedInConfig.json'))
    extract_linkedin_profiles(**cfgs)
