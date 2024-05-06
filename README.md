# Steve Scargall's Personal Blog

Welcome to the repository for Steve Scargall's personal blog, hosted at [stevescargall.com](https://stevescargall.com). This website is built using the [Hugo](https://gohugo.io/) static site generator, leveraging the powerful and flexible HugoPlate theme from [Zeon Studio](https://github.com/zeon-studio/hugoplate).

## Introduction

This blog serves as a platform for Steve to share his thoughts, experiences, and professional insights. The website is designed to be minimalistic yet functional, ensuring content is at the forefront, enhanced by the aesthetic appeal of the HugoPlate theme.

## Prerequisites

Before you begin setting up the site locally, make sure you have the following installed:
- [Hugo Extended v0.124+](https://gohugo.io/installation/)
- [Node v20+](https://nodejs.org/en/download/)
- [Go v1.22+](https://go.dev/doc/install)

## Installation

To get a local copy up and running follow these simple steps.

### Clone the Repository

Start by cloning the repository to your local machine. Open a terminal and run the following command:

```bash
git clone https://github.com/stevescargall/blog.git
cd blog
```

### 👉 Install Dependencies

Install all the dependencies using the following command.

```bash
npm install
```

### 👉 Development Command

Start the development server using the following command.

```bash
npm run dev
```

If you are developing on a remote server, use:

```bash
hugo server --bind 0.0.0.0 --verbose --baseURL http://123.456.7.89 --theme hugoplate
```

where the `baseURL` should be the IP Address or hostname of the remote host.
