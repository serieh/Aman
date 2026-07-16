import { useAuthStore } from '../store/useAuthStore';
import { en } from '../locales/en';
import { ar } from '../locales/ar';

const dictionaries = { en, ar };

export function useTranslation() {
  const language = useAuthStore(state => state.language);
  const currentLang = language === 'ar' ? 'ar' : 'en';
  const dict = dictionaries[currentLang] || en;

  const t = (key, fallbackOrVariables = {}, variables = {}) => {
    let text = dict[key];
    let actualVariables = {};
    let fallback = undefined;

    if (typeof fallbackOrVariables === 'string') {
      fallback = fallbackOrVariables;
      actualVariables = variables;
    } else if (fallbackOrVariables && typeof fallbackOrVariables === 'object') {
      actualVariables = fallbackOrVariables;
    }

    // 1. Fallback to English dictionary if not found in active dictionary
    if (text === undefined && currentLang !== 'en') {
      text = en[key];
    }
    
    // 2. Fallback to default string or raw key if not found anywhere
    if (text === undefined) {
      return fallback !== undefined ? fallback : String(key);
    }

    // 3. Interpolate variables safely
    let result = text;
    if (actualVariables && typeof actualVariables === 'object' && !Array.isArray(actualVariables)) {
      Object.entries(actualVariables).forEach(([varName, val]) => {
        // Escape regex special characters in key to prevent syntax errors
        const escapedVarName = String(varName).replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
        result = result.replace(new RegExp(`{${escapedVarName}}`, 'g'), String(val));
      });
    }

    return result;
  };

  const dir = currentLang === 'ar' ? 'rtl' : 'ltr';

  return { t, dir, lang: currentLang };
}
export default useTranslation;
