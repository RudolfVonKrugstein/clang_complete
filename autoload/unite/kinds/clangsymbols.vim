let s:kind = {
      \ 'name'           : 'clangsymbols',
      \ 'default_action' : 'listlocations',
      \ 'action_table'   : {},
      \ 'parent'         : [],
      \ }

let s:kind.action_table.listlocations = {
      \ 'is_selectable' : 0,
      \ }

function! s:kind.action_table.listlocations.func(candidate)
  call unite#start([['clangsymbollocations', a:candidate.usr, "declarations_and_definitions"]])
endfunction

function! unite#kinds#clangsymbols#define()
  return s:kind
endfunction
