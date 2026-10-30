export function canEdit(user) {
  if ("admin" === user.level) {
    return true;
  }
  return user.editor === true;
}
