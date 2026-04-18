#!/usr/bin/env lua

-- Skills installer — symlinks each skill into ~/.claude/skills/<name>
--
-- Usage:
--   lua install.lua                # dry-run: show plan
--   lua install.lua --apply        # create/update symlinks
--   lua install.lua --list         # list discovered skills and exit
--   lua install.lua --prune        # remove stale symlinks in ~/.claude/skills
--                                  #   (only ones pointing inside this repo)
--   lua install.lua --target DIR   # override target (default ~/.claude/skills)
--
-- Discovery rules:
--   1. Any top-level directory containing SKILL.md  → install as <dir>.
--   2. vendor/<name>/ submodules:
--        - if vendor/<name>/SKILL.md exists, install as <name>.
--        - else walk vendor/<name>/* one level and install each child
--          that contains SKILL.md.
--   3. Directories whose name starts with "_" or "." are ignored.
--   4. A dir containing a .skillignore file is ignored.

-- ============================================================
-- Utilities
-- ============================================================

local home = os.getenv("HOME")

local C = {
  reset  = "\27[0m",
  green  = "\27[32m",
  yellow = "\27[33m",
  blue   = "\27[34m",
  red    = "\27[31m",
  dim    = "\27[2m",
}

local function expand(path)
  if path:sub(1, 1) == "~" then return home .. path:sub(2) end
  return path
end

local function get_script_dir()
  local info = debug.getinfo(1, "S")
  local script_path = info.source:match("^@(.+)$") or arg[0]
  local handle = io.popen('cd "$(dirname "' .. script_path .. '")" && pwd')
  local dir = handle:read("*l")
  handle:close()
  return dir
end

local function path_exists(path)
  local h = io.popen('test -e "' .. path .. '" && echo yes || echo no')
  local r = h:read("*l"); h:close()
  return r == "yes"
end

local function is_dir(path)
  local h = io.popen('test -d "' .. path .. '" && echo yes || echo no')
  local r = h:read("*l"); h:close()
  return r == "yes"
end

local function is_symlink(path)
  local h = io.popen('test -L "' .. path .. '" && echo yes || echo no')
  local r = h:read("*l"); h:close()
  return r == "yes"
end

local function readlink(path)
  local h = io.popen('readlink "' .. path .. '"')
  local r = h:read("*l"); h:close()
  return r
end

local function list_dirs(dir)
  local out = {}
  local h = io.popen('ls -1 "' .. dir .. '" 2>/dev/null')
  if not h then return out end
  for line in h:lines() do
    if is_dir(dir .. "/" .. line) then table.insert(out, line) end
  end
  h:close()
  return out
end

local function ensure_parent(path)
  local dir = path:match("(.+)/[^/]+$")
  if dir then os.execute('mkdir -p "' .. dir .. '"') end
end

local function timestamp() return os.date("%Y%m%d_%H%M%S") end

local function backup(path)
  local bak = path .. ".bak." .. timestamp()
  os.execute('mv "' .. path .. '" "' .. bak .. '"')
  return bak
end

local function create_link(src, dst)
  os.execute('ln -sf "' .. src .. '" "' .. dst .. '"')
end

local function skill_ignored(dir)
  local base = dir:match("([^/]+)$")
  if not base then return true end
  if base:sub(1, 1) == "." or base:sub(1, 1) == "_" then return true end
  if path_exists(dir .. "/.skillignore") then return true end
  return false
end

local function has_skill_md(dir)
  return path_exists(dir .. "/SKILL.md")
end

-- ============================================================
-- Discovery
-- ============================================================

local function discover(root)
  local skills = {}   -- list of { name, src }
  local seen = {}

  local function add(name, src)
    if seen[name] then
      io.stderr:write(C.red .. "conflict: " .. name
        .. " already resolved to " .. seen[name]
        .. ", ignoring " .. src .. C.reset .. "\n")
      return
    end
    seen[name] = src
    table.insert(skills, { name = name, src = src })
  end

  -- Pass 1: top-level dirs
  for _, entry in ipairs(list_dirs(root)) do
    local dir = root .. "/" .. entry
    if entry ~= "vendor" and not skill_ignored(dir) and has_skill_md(dir) then
      add(entry, dir)
    end
  end

  -- Pass 2: vendor/*
  local vendor = root .. "/vendor"
  if is_dir(vendor) then
    for _, entry in ipairs(list_dirs(vendor)) do
      local dir = vendor .. "/" .. entry
      if not skill_ignored(dir) then
        if has_skill_md(dir) then
          add(entry, dir)
        else
          -- collection repo: look one level deeper
          for _, child in ipairs(list_dirs(dir)) do
            local cdir = dir .. "/" .. child
            if not skill_ignored(cdir) and has_skill_md(cdir) then
              add(child, cdir)
            end
          end
        end
      end
    end
  end

  table.sort(skills, function(a, b) return a.name < b.name end)
  return skills
end

-- ============================================================
-- CLI
-- ============================================================

local function parse_args()
  local opts = { apply = false, list = false, prune = false, target = "~/.claude/skills" }
  local i = 1
  while i <= #arg do
    local a = arg[i]
    if a == "--apply" then opts.apply = true
    elseif a == "--list" then opts.list = true
    elseif a == "--prune" then opts.prune = true
    elseif a == "--target" then i = i + 1; opts.target = arg[i]
    elseif a:match("^--target=") then opts.target = a:match("^--target=(.+)$")
    elseif a == "--help" or a == "-h" then
      print("Usage: lua install.lua [--apply] [--list] [--prune] [--target DIR]")
      os.exit(0)
    else
      io.stderr:write("Unknown argument: " .. a .. "\n"); os.exit(1)
    end
    i = i + 1
  end
  return opts
end

-- ============================================================
-- Main
-- ============================================================

local function main()
  local opts = parse_args()
  local root = get_script_dir()
  local target = expand(opts.target)
  local skills = discover(root)

  if opts.list then
    for _, s in ipairs(skills) do
      print(string.format("%s\t%s", s.name, s.src:gsub("^" .. root .. "/", "")))
    end
    return
  end

  print("")
  print(C.blue .. "skills installer" .. C.reset)
  print(C.dim .. string.rep("─", 60) .. C.reset)
  print("  Repo:   " .. root)
  print("  Target: " .. target)
  print("  Mode:   " .. (opts.apply and (C.yellow .. "APPLY" .. C.reset) or (C.dim .. "dry-run" .. C.reset)))
  print("  Found:  " .. #skills .. " skill(s)")
  print(C.dim .. string.rep("─", 60) .. C.reset)
  print("")

  local actions = {}

  for _, s in ipairs(skills) do
    local dst = target .. "/" .. s.name
    local action = { src = s.src, dst = dst, name = s.name, op = "create" }
    if is_symlink(dst) then
      local t = readlink(dst)
      if t == s.src then action.op = "skip"
      else action.op = "update"; action.old_target = t end
    elseif path_exists(dst) then
      action.op = "backup"
    end
    table.insert(actions, action)
  end

  -- Prune: symlinks in target that point into this repo but aren't in skills.
  local prune_actions = {}
  if opts.prune and is_dir(target) then
    local want = {}
    for _, s in ipairs(skills) do want[s.name] = true end
    for _, entry in ipairs(list_dirs(target)) do
      local p = target .. "/" .. entry
      if is_symlink(p) then
        local t = readlink(p) or ""
        if t:sub(1, #root) == root and not want[entry] then
          table.insert(prune_actions, { dst = p, op = "prune", old_target = t })
        end
      end
    end
  end

  local function label_for(op)
    if op == "skip"   then return "SKIP",   C.dim end
    if op == "create" then return "CREATE", C.green end
    if op == "update" then return "UPDATE", C.yellow end
    if op == "backup" then return "BACKUP", C.red end
    if op == "prune"  then return "PRUNE",  C.red end
  end

  for _, a in ipairs(actions) do
    local label, color = label_for(a.op)
    print(string.format("  %s[%-6s]%s  %s → %s", color, label, C.reset, a.dst, a.src))
    if a.op == "update" then
      print(string.format("           %swas → %s%s", C.dim, a.old_target, C.reset))
    end
  end
  for _, a in ipairs(prune_actions) do
    local label, color = label_for(a.op)
    print(string.format("  %s[%-6s]%s  %s  (was → %s)", color, label, C.reset, a.dst, a.old_target))
  end

  print("")
  if not opts.apply then
    print(C.dim .. "Dry run. Pass --apply to execute." .. C.reset)
    return
  end

  local created, updated, backed_up, skipped, pruned = 0, 0, 0, 0, 0

  os.execute('mkdir -p "' .. target .. '"')

  for _, a in ipairs(actions) do
    if a.op == "skip" then
      skipped = skipped + 1
    else
      ensure_parent(a.dst)
      if a.op == "backup" then
        local bak = backup(a.dst)
        print(C.yellow .. "  backed up: " .. a.dst .. " → " .. bak .. C.reset)
        backed_up = backed_up + 1
      elseif a.op == "update" then
        os.execute('rm "' .. a.dst .. '"')
        updated = updated + 1
      else
        created = created + 1
      end
      create_link(a.src, a.dst)
    end
  end

  for _, a in ipairs(prune_actions) do
    os.execute('rm "' .. a.dst .. '"')
    pruned = pruned + 1
  end

  print("")
  print(C.green .. "Done!" .. C.reset
    .. " created=" .. created
    .. " updated=" .. updated
    .. " backed_up=" .. backed_up
    .. " skipped=" .. skipped
    .. " pruned=" .. pruned)
end

main()
