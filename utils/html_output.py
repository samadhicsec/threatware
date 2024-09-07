import logging
import jsonpickle
from lxml import etree
import lxml.html
from lxml.etree import XPathError


def set_html_output(format, issues, html_doc):

    if format != "html":
        return

    document = lxml.html.document_fromstring(html_doc)

    showing_all_errors = True

    if len(issues) > 0:
        ##
        # Content to add specific elements
        ##
        # Add the threatwarefinding attribute to the location associated with the finding (if there is one).  This should probably be an array as there could be multiple findings.
        finding_id_count = -1
        for issue in issues:
            try:
                finding_id_count += 1
                xpath = issue.issue_key.properties.get("location", "")
                if xpath == "":
                    showing_all_errors = False
                    continue
                element = document.xpath(xpath)
                element[0].attrib["threatwarefinding"] = f"{finding_id_count}"
            except XPathError:
                logging.warning(f"Could not find location {xpath} in the document")
            except IndexError:
                logging.warning(f"Could not find location {xpath} in the document")

        ##
        # Content to add to the very end of the body element
        ##
        body_element = document.xpath("//html/body")[0]

        # Add the script includes for tippy
        etree.SubElement(body_element, "script", src="https://unpkg.com/@popperjs/core@2.9.3/dist/umd/popper.min.js")
        etree.SubElement(body_element, "script", src="https://unpkg.com/tippy.js@6/dist/tippy-bundle.umd.js")
        etree.SubElement(body_element, "link", rel="stylesheet", href="https://unpkg.com/tippy.js@6/themes/light.css")
        etree.SubElement(body_element, "link", rel="stylesheet", href="https://unpkg.com/tippy.js@6/themes/light-border.css")
        etree.SubElement(body_element, "link", rel="stylesheet", href="https://unpkg.com/tippy.js@6/themes/material.css")
        etree.SubElement(body_element, "link", rel="stylesheet", href="https://unpkg.com/tippy.js@6/themes/translucent.css")
        etree.SubElement(body_element, "link", rel="stylesheet", href="https://unpkg.com/tippy.js@6/animations/scale.css")
        
        # Add the threatware findings as a json variable
        json_issues = jsonpickle.encode(issues, unpicklable=False)
        findings = etree.SubElement(body_element, "script")
        findings.text = f"var threatwarefindings = {json_issues}"
        
        # Add CSS for elements with the threatwarefinding attribute
        #    - Need to actually add additional attribute to style Errors vs Warnings with a different colour
        findings_css = etree.SubElement(body_element, "style", type="text/css")
        findings_css.text = """
            [threatwarefinding] {
                background-color: red
            }
        """
        
        # Add the tippy script to make the tooltip show
        #    - Needs to support showing multiple findings
        tippy_script = etree.SubElement(body_element, "script")
        tippy_script.text = """
        function formatfinding(finding) {
                return `<div>
                <h3>${finding["type"]}</h3>
                <p>${finding["error-description"]}</p>
                <p>${finding["fix-description"]}</p>
                </div>`
            }
            // With the above scripts loaded, you can call `tippy()` with a CSS
            // selector and a `content` prop:
            tippy('[threatwarefinding]', {
            theme: 'light-border',
            animation: 'scale',
            placement: 'right',
            content(reference) {
                const id = reference.getAttribute('threatwarefinding');
                //const template = document.getElementById(id);
                const template = formatfinding(threatwarefindings[id]);
                return template;
            },
            allowHTML: true,
            });
        </script>
        """

    ##
    # Content to add to the top of the document.  This might change depending on teh success we have adding content elsewhere
    ##
    # Add a banner to the top of the body saying whether the validation passed, failed,or failed and not all errors are shown

    if len(issues) > 0:
        if showing_all_errors:
            banner_msg = "Errors were found.  Any entry in the threat model coloured red will display the error when you hover over it."
        else:
            banner_msg = """
            Errors were found.  Any entry in the threat model coloured red will display the error when you hover over it.
            
            Not all of them are shown
            """
    else:
        banner_msg = "No errors were found"

    banner_script = etree.SubElement(body_element, "script")
    banner_script.text = f"""
    configObj = {{
        "text": "{banner_msg}",
        "bannerURL": "",
        "selectedBackgroundColor": "#69C3FF",
        "selectedTextColor": "#181818",
        "bannerHeight": "64px",
        "fontSize": "15px"
    }};

    function createBanner(obj, pageSimulator) {{
        var swBannerLink = obj.bannerURL;
        var swBannerTarget = "_blank";
        var swBannerText = obj.text;
        var body = document.body;
        var swBanner = document.createElement('a');
        var centerDiv = document.createElement('div');
        var text = document.createElement('span');

        swBanner.href = swBannerLink;
        swBanner.target = swBannerTarget;
        swBanner.style.display = "flex";
        swBanner.style.justifyContent = "center";
        swBanner.style.alignItems = "center";
        swBanner.style.width = "100%";
        swBanner.style.minHeight = "48px";
        swBanner.style.maxHeight = "72px";
        swBanner.style.paddingTop = "8px";
        swBanner.style.paddingBottom = "8px";
        swBanner.style.paddingLeft = "20px";
        swBanner.style.paddingRight = "20px";
        swBanner.style.lineHeight = "18px";
        swBanner.style.textAlign = "center";
        swBanner.style.textDecoration = "none";
        swBanner.style.height = obj.bannerHeight;
        swBanner.style.fontSize = obj.fontSize;
        text.innerHTML = swBannerText;
        swBanner.style.backgroundColor = obj.selectedBackgroundColor;
        swBanner.style.color = obj.selectedTextColor;
        swBanner.id = 'sw-banner';
        swBanner.classList.add('sw-banner');
        centerDiv.classList.add('center');
        centerDiv.append(text);
        swBanner.append(centerDiv);

        body.insertBefore(swBanner, body.firstChild);
    }}

    document.addEventListener("DOMContentLoaded", function () {{
        createBanner(configObj, null);
    }});
    
    """

    new_html_bstr = lxml.html.tostring(document, encoding='unicode')
    new_html_str = new_html_bstr

    # Add "<!doctype html>" to the top of the page.  This tells the brwoser to use standards mode.  This is important as the browser will use quirks mode if this is not present.
    new_html_str = "<!doctype html>\n" + new_html_str
    

    return new_html_str

