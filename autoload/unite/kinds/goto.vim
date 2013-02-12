let s:kind = {
      \ 'name'           : 'goto',
      \ 'default_action' : 'goto',
      \ 'action_table'   : {},
      \ 'parent'         : [],
      \ }

let s:kind.action_table.goto = {
      \ 'is_selectable' : 0,
      \ }

function! s:kind.action_table.goto.func(candidate)
  execute "edit" a:candidate.file
  call cursor (a:candidate.line, a:candidate.column)
endfunction

function! unite#kinds#goto#define()
  return s:kind
endfunction
