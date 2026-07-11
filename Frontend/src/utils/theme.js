export const THEME_STORAGE_KEY = 'aman-theme-pref';

export function applyTheme(themeStr) {
  if (typeof document === 'undefined') return;
  
  const finalThemeStr = themeStr || 'sunrise-light';
  const parts = finalThemeStr.split('-');
  const themeName = parts[0] || 'sunrise';
  const mode = parts[1] || 'light';

  const validThemes = ['sunrise', 'original', 'sunset', 'ocean'];
  const finalTheme = validThemes.includes(themeName) ? themeName : 'sunrise';
  const finalMode = (mode === 'dark' || mode === 'light') ? mode : 'light';

  document.documentElement.setAttribute('data-theme', finalTheme);
  
  if (finalMode === 'dark') {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }
}
