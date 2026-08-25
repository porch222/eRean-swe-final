import 'package:flutter/material.dart';

class T {
  static const n0 = Color(0xFFFFFFFF);
  static const n25 = Color(0xFFFCFBF9);
  static const n50 = Color(0xFFF8F7F5);
  static const n100 = Color(0xFFF1EFEB);
  static const n200 = Color(0xFFE7E4DE);
  static const n300 = Color(0xFFD5D0C7);
  static const n400 = Color(0xFF9D968A);
  static const n500 = Color(0xFF6F6A61);
  static const n600 = Color(0xFF514D46);
  static const n800 = Color(0xFF232C3C);
  static const n900 = Color(0xFF131A26);

  static const brand50 = Color(0xFFF8EEF1);
  static const brand500 = Color(0xFF93304C);
  static const brand600 = Color(0xFF7A2740);
  static const brand700 = Color(0xFF5E1C31);

  static const brass50 = Color(0xFFF9F2E4);
  static const brass600 = Color(0xFFA97C2F);

  static const ok50 = Color(0xFFE9F1EC);
  static const ok600 = Color(0xFF2F6F4F);
  static const warn50 = Color(0xFFF9F2E4);
  static const warn600 = Color(0xFFA97C2F);
  static const bad50 = Color(0xFFF8ECEC);
  static const bad600 = Color(0xFFA33232);
  static const info50 = Color(0xFFECEFF5);
  static const info600 = Color(0xFF3D5480);

  static const s1 = 4.0;
  static const s2 = 8.0;
  static const s3 = 12.0;
  static const s4 = 16.0;
  static const s5 = 24.0;
  static const s6 = 32.0;

  static const radius = 10.0;
  static const radiusLg = 14.0;
}

const TextStyle kNumeric = TextStyle(
  fontFeatures: [FontFeature.tabularFigures()],
  fontFamily: 'Arial',
);

ThemeData buildTheme() {
  final base = ThemeData(
    fontFamily: 'Arial',
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(
      seedColor: T.brand600,
      primary: T.brand600,
      surface: T.n0,
      error: T.bad600,
    ),
    scaffoldBackgroundColor: T.n50,
  );

  return base.copyWith(
    appBarTheme: const AppBarTheme(
      backgroundColor: T.n0,
      foregroundColor: T.n900,
      elevation: 0,
      scrolledUnderElevation: 0.5,
      centerTitle: false,
      titleTextStyle: TextStyle(
        color: T.n900,
        fontSize: 19,
        fontWeight: FontWeight.w600,
      ),
    ),
    cardTheme: CardThemeData(
      color: T.n0,
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(T.radiusLg),
        side: const BorderSide(color: T.n200),
      ),
    ),
    dividerTheme: const DividerThemeData(color: T.n200, thickness: 1, space: 1),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: T.brand600,
        foregroundColor: T.n0,

        minimumSize: const Size.fromHeight(48),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(T.radius),
        ),
        textStyle: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: T.brand600,
        minimumSize: const Size.fromHeight(48),
        side: const BorderSide(color: T.n300),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(T.radius),
        ),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: T.n0,
      contentPadding: const EdgeInsets.symmetric(
        horizontal: T.s4,
        vertical: T.s3,
      ),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(T.radius),
        borderSide: const BorderSide(color: T.n300),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(T.radius),
        borderSide: const BorderSide(color: T.n300),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(T.radius),
        borderSide: const BorderSide(color: T.brand600, width: 1.5),
      ),
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: T.n0,
      indicatorColor: T.brand50,
      elevation: 3,
      height: 64,
      labelTextStyle: WidgetStateProperty.resolveWith(
        (states) => TextStyle(
          fontSize: 11.5,
          fontWeight: states.contains(WidgetState.selected)
              ? FontWeight.w600
              : FontWeight.w500,
          color: states.contains(WidgetState.selected) ? T.brand700 : T.n500,
        ),
      ),
      iconTheme: WidgetStateProperty.resolveWith(
        (states) => IconThemeData(
          size: 24,
          color: states.contains(WidgetState.selected) ? T.brand700 : T.n500,
        ),
      ),
    ),
  );
}
