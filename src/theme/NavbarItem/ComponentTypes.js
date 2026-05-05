import ComponentTypes from '@theme-original/NavbarItem/ComponentTypes';
import LanguageSwitcherNavbarItem from '@site/src/components/LanguageSwitcherNavbarItem';
import LocaleAwareNavbarItem from '@site/src/components/LocaleAwareNavbarItem';

export default {
  ...ComponentTypes,
  'custom-languageSwitcher': LanguageSwitcherNavbarItem,
  'custom-localeAwareLink': LocaleAwareNavbarItem,
};
