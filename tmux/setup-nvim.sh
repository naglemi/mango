#!/usr/bin/env bash
# Setup NeoVim with file browser configuration

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NVIM_CONFIG_DIR="$HOME/.config/nvim"

echo " Setting up NeoVim with file browser..."

# Create config directory
mkdir -p "$NVIM_CONFIG_DIR"

# Copy init.lua configuration
cat > "$NVIM_CONFIG_DIR/init.lua" << 'EOF'
-- NeoVim Configuration with File Browser
-- Bootstrap lazy.nvim plugin manager
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not vim.loop.fs_stat(lazypath) then
  vim.fn.system({
    "git",
    "clone",
    "--filter=blob:none",
    "https://github.com/folke/lazy.nvim.git",
    "--branch=stable",
    lazypath,
  })
end
vim.opt.rtp:prepend(lazypath)

-- Basic settings
vim.opt.number = true           -- Show line numbers
vim.opt.relativenumber = true   -- Show relative line numbers
vim.opt.mouse = 'a'             -- Enable mouse support
vim.opt.ignorecase = true       -- Case insensitive searching
vim.opt.smartcase = true        -- Case sensitive if uppercase present
vim.opt.termguicolors = true    -- True color support

-- Plugin setup
require("lazy").setup({
  -- File explorer
  {
    "nvim-tree/nvim-tree.lua",
    dependencies = {
      "nvim-tree/nvim-web-devicons", -- File icons
    },
    config = function()
      require("nvim-tree").setup({
        sort_by = "case_sensitive",
        view = {
          width = 35,
        },
        renderer = {
          group_empty = true,
          icons = {
            show = {
              file = true,
              folder = true,
              folder_arrow = true,
              git = true,
            },
          },
        },
        filters = {
          dotfiles = false,
        },
      })
    end,
  },

  -- Color scheme
  {
    "folke/tokyonight.nvim",
    lazy = false,
    priority = 1000,
    config = function()
      vim.cmd([[colorscheme tokyonight-night]])
    end,
  },
})

-- Key mappings
vim.g.mapleader = " "  -- Set leader key to space

-- File explorer toggle
vim.keymap.set('n', '<leader>e', ':NvimTreeToggle<CR>', { noremap = true, silent = true, desc = "Toggle file explorer" })
vim.keymap.set('n', '<C-n>', ':NvimTreeToggle<CR>', { noremap = true, silent = true, desc = "Toggle file explorer" })

-- Open file explorer on startup if no file specified
vim.api.nvim_create_autocmd("VimEnter", {
  callback = function()
    if vim.fn.argc() == 0 then
      vim.cmd("NvimTreeOpen")
    end
  end,
})
EOF

echo " NeoVim configuration written to $NVIM_CONFIG_DIR/init.lua"

# Check if nvim is installed
if ! command -v nvim &> /dev/null; then
    echo ""
    echo "  NeoVim not found. Installing..."

    # Check OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt-get &> /dev/null; then
            echo "Installing via apt..."
            sudo apt-get update && sudo apt-get install -y neovim
        elif command -v yum &> /dev/null; then
            echo "Installing via yum..."
            sudo yum install -y neovim
        else
            echo " Unable to auto-install. Please install neovim manually:"
            echo "   https://github.com/neovim/neovim/releases"
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            echo "Installing via Homebrew..."
            brew install neovim
        else
            echo " Homebrew not found. Please install neovim manually:"
            echo "   https://github.com/neovim/neovim/releases"
            exit 1
        fi
    fi
fi

# Install plugins on first run
echo ""
echo " Installing NeoVim plugins (this may take a moment)..."
nvim --headless "+Lazy! sync" +qa 2>/dev/null || true

echo ""
echo " NeoVim setup complete!"
echo ""
echo "Key bindings:"
echo "  <Space>e or Ctrl+n: Toggle file browser"
echo "  <Space> is the leader key"
echo ""
echo "Try it: nvim"
