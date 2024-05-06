---
title: "A Quick Guide to Signing Your Git Commits"
date: "2020-02-04"
categories: 
  - "how-to"
tags: 
  - "git"
  - "gpg"
image: "images/git-gpg.png"
---

It is important to sign Git commits for your source code to avoid the code being compromised and to confirm to the repository gatekeeper that you are who you say you are. Signing guarantees that my code is my work, it is my copyright and nobody else can fake it. This guide provides the necessary steps to creating private & public keys so you can sign your Git commits.

On Linux or Mac, if you have setup a development environment then you have all the necessary tools for signing.

## 1\. Show the current configuration

You can use either of the following to display the configuration:

```
git config --list
git config -l
```

or look at your `~/.gitconfig` file. The local configuration will be in your repository's `.git/config` file.

Use:

```
git config --list --show-origin
```

to see where that setting is defined (global, user, repo, etc...).

Alternatively, you can filter the results, using `--global`, `--local`, and `--system`:

```
git config --list --global
git config --list --local
git config --list --system
```

To edit a configuration, use:

```
git config --global --edit
git config --local --edit
git config --system --edit
```

This will drop you into your default editor where you can add, remove, or make changes to entries.

## 2\. Set your name and email address

If you haven't already configured your name and email address within Git, use the following to make changes to the local Git project:

```
git config user.name 'Steve Scargall'
git config user.email 'noreply@stevescargall.com'
```

If you want to make the changes apply across all Git projects, use:

```
git config --global user.name 'Steve Scargall'
git config --global user.email 'noreply@stevescargall.com'
```

## 3\. Generate a GPG key pair

Use the following `gpg` command to interactively create the public/private key pair:

```
gpg --full-generate-key
```

Use the maximum key size available, likely 4096, and ensure the key does not expire. You'll be prompted with several questions shown below:

```
$ gpg --full-generate-key
gpg (GnuPG) 2.2.17; Copyright (C) 2019 Free Software Foundation, Inc.
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.

Please select what kind of key you want:
   (1) RSA and RSA (default)
   (2) DSA and Elgamal
   (3) DSA (sign only)
   (4) RSA (sign only)
Your selection? 1
RSA keys may be between 1024 and 4096 bits long.
What keysize do you want? (2048) 4096
Requested keysize is 4096 bits
Please specify how long the key should be valid.
         0 = key does not expire
      <n>  = key expires in n days
      <n>w = key expires in n weeks
      <n>m = key expires in n months
      <n>y = key expires in n years
Key is valid for? (0) 0
Key does not expire at all
Is this correct? (y/N) y

GnuPG needs to construct a user ID to identify your key.

Real name: Steve Scargall
Email address: noreply@stevescargall.com
Comment: GitHub
You selected this USER-ID:
    "Steve Scargall (GitHub) <noreply@stevescargall.com>"

Change (N)ame, (C)omment, (E)mail or (O)kay/(Q)uit? O

[...key is generated and displayed here...]
```

## 4\. List your key(s)

To make sure your GPG key pair is created, run following command and verify output.

```
gpg --list-secret-keys --keyid-format LONG
```

You will see something similar to this:

```
$ gpg --list-secret-keys --keyid-format LONG
gpg: checking the trustdb
gpg: marginals needed: 3  completes needed: 1  trust model: pgp
gpg: depth: 0  valid:   1  signed:   0  trust: 0-, 0q, 0n, 0m, 0f, 1u
/root/.gnupg/pubring.kbx
------------------------
sec   rsa4096/3AC5D24571557BB1 2020-02-04 [SC]
      21BB8B2D82228D9CC0049A193AC5D24571557BB1
uid                 [ultimate] Steve Scargall (GitHub) <noreply@stevescargall.com>
ssb   rsa4096/9FB9DAD85D7623D6 2020-02-04 [E]
```

Copy the key ID from the output. The key ID in the above example is **3AC5D24571557BB1** or you can use **21BB8B2D82228D9CC0049A193AC5D24571557BB1**.

## 5\. Add the key to GitHub

Display your public key on the terminal:

```
gpg --armor --export 3AC5D24571557BB1
```

It will display the GPG key including both header and footer text, something like this:

```
-----BEGIN PGP PUBLIC KEY BLOCK-----
KEY_CONTENT....
-----END PGP PUBLIC KEY BLOCK-----
```

Launch [GitHub](https://github.com/) in a web browser.

Navigate to [Settings > SSH and GPG keys](https://github.com/settings/keys).

Click the green button to [add New GPG Key](https://github.com/settings/gpg/new).

Copy and paste the public key from the `gpg --armor --export 3AC5D24571557BB1` command and click the green 'Add GPG key' button.

## 6\. Configure the GPG program in Git

To sign your git commits, you will need to specify a GPG program. Try following commands

```
// on Windows
$ git config --global gpg.program "/c/Program Files (x86)/GnuPG/bin/gpg.exe"

// on Linux or Mac
$ which gpg
/usr/local/bin/gpg
$ git config --global gpg.program "/usr/local/bin/gpg"
```

## 7\. Configure Git to auto-sign every commit

To specify a key for auto-sign commits in a single repository, execute these commands:

```
git config user.signingkey 3AC5D24571557BB1 
git config commit.gpgsign true
```

If you want to use this GPG key ID for all Git repositories use the `--global` option.

```
git config --global user.signingkey 3AC5D24571557BB1 
git config --global commit.gpgsign true
```

If you do not want to auto-sign every commit, you do not have to run the above commands. Instead, you can sign individual commits using (-S) and add a "Signed-off-by" signature with (-s):

```
git commit -s -S -m "your commit message"
```

## 8\. Disable TTY for GPG

To avoid the following error:

```
$ git commit -m "My Message"
error: gpg failed to sign the data
fatal: failed to write commit object
```

I found that I had to disable TTY for gpg using:

```
echo 'no-tty' >> ~/.gnupg/gpg.conf
```

I also found the following helped:

```
export GPG_TTY=$(tty)
```

So I added an entry in my `/etc/environment` to apply the change to all users.

For more troubleshooting ideas, check this [StackOverflow](https://stackoverflow.com/questions/39494631/gpg-failed-to-sign-the-data-fatal-failed-to-write-commit-object-git-2-10-0) thread.

## Summary

This blog post showed you how to create a public/private key pair using `gpg` then upload your key to GitHub, and finally how to manually or automatically sign git commits.
