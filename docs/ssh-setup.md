# SSH Setup for Longleaf

This guide walks you through setting up SSH keys so you can connect to Longleaf without typing your password every time. It also configures an SSH alias so you can just type `ssh longleaf` instead of the full hostname.

Pick the section for your operating system, then continue with the shared steps at the end.

## Windows

### 1a. Install a terminal

You have two good options:

- **Windows Terminal + PowerShell** (built into Windows 10/11). Open "Terminal" from the Start menu.
- **WSL (Windows Subsystem for Linux)** if you prefer a Linux environment. Install it with `wsl --install` in PowerShell, then follow the macOS/Linux instructions below from inside WSL.

The instructions below use PowerShell. If you're using WSL, follow the macOS/Linux section instead.

### 1b. Generate an SSH key

Open PowerShell and run:

```powershell
ssh-keygen -t ed25519 -C "your_onyen@email.unc.edu"
```

Press Enter to accept the default file location (`C:\Users\YourName\.ssh\id_ed25519`). Set a passphrase if you want, or press Enter for none.

### 1c. Copy your public key to Longleaf

Windows doesn't have `ssh-copy-id`. Instead, run this in PowerShell (all one command):

```powershell
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh your_onyen@longleaf.unc.edu "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

Type your Longleaf password one last time.

Test it:

```powershell
ssh your_onyen@longleaf.unc.edu
```

### 1d. Set up an SSH config alias

Create or edit `C:\Users\YourName\.ssh\config` (no file extension) with Notepad or VS Code:

```
Host longleaf
    HostName longleaf.unc.edu
    User your_onyen
    IdentityFile ~/.ssh/id_ed25519
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

Replace `your_onyen` with your actual ONYEN. Now you can connect with:

```powershell
ssh longleaf
```

### 1e. Set up the SSH agent (optional)

To avoid re-entering your passphrase, start the SSH agent service. In an elevated (admin) PowerShell:

```powershell
Get-Service ssh-agent | Set-Service -StartupType Automatic
Start-Service ssh-agent
ssh-add $env:USERPROFILE\.ssh\id_ed25519
```

## macOS / Linux

### 2a. Generate an SSH key

Skip this if you already have a key at `~/.ssh/id_ed25519`.

```bash
ssh-keygen -t ed25519 -C "your_onyen@email.unc.edu"
```

Press Enter to accept the default file location. Set a passphrase if you want (recommended), or press Enter for none.

### 2b. Copy your public key to Longleaf

```bash
ssh-copy-id your_onyen@longleaf.unc.edu
```

Type your Longleaf password one last time. After this, key-based login is enabled.

Test it:

```bash
ssh your_onyen@longleaf.unc.edu
```

You should get in without a password prompt (or with just your key passphrase if you set one).

### 2c. Set up an SSH config alias

Edit (or create) `~/.ssh/config` on your laptop:

```
Host longleaf
    HostName longleaf.unc.edu
    User your_onyen
    IdentityFile ~/.ssh/id_ed25519
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

Replace `your_onyen` with your actual ONYEN. Now you can connect with just:

```bash
ssh longleaf
```

The `ServerAliveInterval` and `ServerAliveCountMax` settings send a keepalive ping every 60 seconds, which prevents idle disconnects.

### 2d. Set up an SSH agent (optional, macOS)

If you set a passphrase on your key, you can store it in the macOS Keychain so you only enter it once per reboot.

Add to `~/.ssh/config`:

```
Host *
    AddKeysToAgent yes
    UseKeychain yes
```

Then add your key to the agent:

```bash
ssh-add --apple-use-keychain ~/.ssh/id_ed25519
```

On Linux, most desktop environments run an SSH agent automatically. You can add your key with `ssh-add ~/.ssh/id_ed25519`.

## Clone this repo on Longleaf

Once SSH is set up, connect and clone:

```bash
ssh longleaf
git clone https://github.com/mckay-lab/longleaf-af3.git
cd longleaf-af3
```

If you want to push changes back, you can set up a GitHub SSH key on Longleaf the same way (generate a key on Longleaf, add the public key to your GitHub account under Settings > SSH Keys).

## Troubleshooting

**"Permission denied (publickey)"**: Your key wasn't copied correctly. On macOS/Linux, run `ssh-copy-id` again. On Windows, re-run the `type ... | ssh` command from step 1c. You can also manually check that `~/.ssh/authorized_keys` on Longleaf contains your public key.

**Connection drops after a few minutes**: Make sure `ServerAliveInterval 60` is in your SSH config.

**"Too many authentication failures"**: If you have many SSH keys, specify the correct one explicitly with `IdentityFile` in your config (already done above).

**Windows: "ssh-keygen is not recognized"**: Make sure OpenSSH is installed. Go to Settings > Apps > Optional Features and add "OpenSSH Client". It's included by default on Windows 10 1809+ and Windows 11.
