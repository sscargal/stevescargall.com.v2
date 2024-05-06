+++
# Post Title - Auto-generated from the file name
title = "pmem.io website"

# Post creation date
date = 2020-01-25T19:54:35Z

# Post is a Draft = True|False
draft = false

# Authors. Comma separated list, e.g. `["Bob Smith", "David Jones"]`.
authors = ["Steve Scargall"]

# Tags and categories
# For example, use `tags = []` for no tags, or the form `tags = ["A Tag", "Another Tag"]` for one or more tags.
tags = ["Persistent Memory","PMem", "Website"]
categories = ["Projects"]

# Featured Image
image = 'pmem.io-screenshot.png'
+++


Today, I'm diving into the process of designing and building PMem.io, the website for the Persistent Memory Development Kit (PMDK). We'll explore how we migrated the site from Jekyll to Hugo, a static site generator, and crafted a custom Tailwind CSS theme to support the new website's features.

## Requirements

Before diving in, let's outline the key requirements we wanted for the updated PMem.io website:

- Improved User Experience (UX): A clean, modern, intuitive, and responsive design that caters to users from diverse technical backgrounds.
- Content Management: A user-friendly content management system (CMS) to simplify content creation and updates.
- Documentation Integration: Seamless integration with existing PMDK documentation for easy access.
- Community Building: Features to foster interaction and collaboration within the PMDK community.
- Static website for speed as there's no dynamic content.
- Fast SSG build time.
- Improved searchability.

We chose to migrate PMem.io from Jekyll to Hugo for several reasons:

- Speed and Performance: Hugo offers superior build times compared to Jekyll.
- Scalability: Hugo's architecture is better suited for handling a growing website with a large volume of content.
- Flexibility: Hugo's templating system provides greater flexibility for creating custom layouts and functionalities.

To achieve the desired UI/UX for PMem.io, we opted for a custom Tailwind CSS theme. Here's why Tailwind was a great fit:

- Rapid Development: Tailwind's utility-first approach allowed for faster development and easier maintenance of the website's styles.
- Customization: Tailwind provides granular control over styles, enabling the creation of a unique and consistent design for PMem.io.
- Responsiveness: Tailwind's built-in responsiveness ensured the website adapts seamlessly to different screen sizes.

You can visit [pmem.io](https://pmem.io/) to see the live website or the [pmem.github.io](https://github.com/pmem/pmem.github.io) repository to see how it's built. The website uses [GitHub Pages](https://pages.github.com/) as the build and hosting solution.