# Setting Up GitHub Pages for SmartFill.AI

This guide will help you enable GitHub Pages for your SmartFill.AI repository.

## Steps to Enable GitHub Pages

1. Go to your GitHub repository at https://github.com/zyxcambridge/autofilltable

2. Click on the "Settings" tab at the top of the repository page
   ![Settings Tab](https://docs.github.com/assets/cb-27528/mw-1440/images/help/repository/repo-actions-settings.webp)

3. In the left sidebar, click on "Pages"
   ![Pages Section](https://docs.github.com/assets/cb-47267/mw-1440/images/help/pages/pages-tab.webp)

4. Under "Build and deployment" > "Source", select "Deploy from a branch"
   
5. Under "Branch", select "main" and "/docs" folder
   ![Branch Selection](https://docs.github.com/assets/cb-86795/mw-1440/images/help/pages/publishing-source-drop-down.webp)

6. Click "Save"

7. Wait a few minutes for GitHub to build and deploy your site

8. Once deployed, you'll see a message saying "Your site is live at https://zyxcambridge.github.io/autofilltable/"

## Accessing Your GitHub Pages Site

After the site is deployed, you can access it at:

https://zyxcambridge.github.io/autofilltable/

## Updating Your GitHub Pages Site

To update your GitHub Pages site:

1. Make changes to the files in the `docs/` directory
2. Commit and push the changes to GitHub
3. GitHub will automatically rebuild and deploy your site

## Customizing Your Site

You can customize your site by editing the following files:

- `docs/index.html`: The main HTML file
- `docs/css/styles.css`: The CSS styles
- `docs/js/main.js`: JavaScript functionality
- `docs/assets/images/`: Directory for images

## Troubleshooting

If your site doesn't appear after enabling GitHub Pages:

1. Check that you've selected the correct branch and folder
2. Ensure that your repository is public
3. Wait a few minutes for GitHub to build and deploy your site
4. Check for any build errors in the GitHub Pages section of your repository settings
