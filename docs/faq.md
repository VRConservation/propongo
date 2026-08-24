# FAQ

## Free and open source?
Propongo is an open source app. The current beta testing of Propongo is free and will stay that way. If we change any of the levels of use to a subscription or fee, we will let users know well in advance. In the near term, we hope to cover costs of development and maintenance and encourage users to contribute at [ko-fi](https://ko-fi.com/propongo). 

We also hope that use for underserved communities, startup businesses, and nonprofits will remain free, but there will be a subscription for those users with the revenue to pay. There will also likely be a future charge for storage, especially beyond certain byte levels, for users that have a lot of proposals, many photos, and a lot of geospatial data. 

## How do I export to PDF?
Click the "Export PDF" button in the Preview tab. PDF export requires GTK3 to be installed.

## AI capabilities?
Yes, but not for generating the written content. We think that proposals written by AI are bound to get rejected by funders and reviewers, or AI reviewers will be able to easily sniff them out for being too general, generic, and inauthentic. Besides, who is better than you to write about your business, organization, and the project you want to fund?

That said, we do believe that AI should help you automate the boring stuff or act as an assistant to help make proposal generation easier. We are currently developing an AI agent within Propongo that will read RFPs and extract the required sections for proposal submittal. Other features could include creating a timeline to submit proposal components in a timely fashion.

## Online proposal submission?
We hope to create API links to frequently used online proposal submission portals so you can develop your proposal, then click a button to submit when you're ready, and the proposal will go to the right place with confirmation. We believe that cutting and pasting proposals into online submission platforms is so 1990's and has no place in the 21st century, when automated solutions should avoid this form of medieval torture and waste of time.

## Customization?
In a word, yes. We hope to add features that allow you to import your logo, brand materials, and photo for your bio in upcoming versions.

## Import Excel data?
Go to the Custom Sections tab, click "Import Excel", and select your `.xlsx` or `.xls` file. The data will be automatically converted to a Markdown table.

## Where are proposals saved?
1. On Linux machines, proposals are saved as JSON files in `app/data/proposals/`. They auto-save as you work after you save them under Save as in the hamburger menu. 
2. For Windows users, proposals are saved in the Documents folder at C:\Users\<username>\Documents\Propongo\proposals.
3. For MacOS users, proposals are saved in the Documents folder.