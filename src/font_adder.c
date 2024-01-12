/* gcc font_adder.c -o libfontadder.so -shared -lfontconfig */

#include <fontconfig/fontconfig.h>
#include <stdio.h>

int fontmain(char *fontdesc) {

    FcInit();

    const FcChar8 *file = (const FcChar8*)fontdesc;
    FcBool fontAddStatus = FcConfigAppFontAddFile(FcConfigGetCurrent(), file);

    if(fontAddStatus == FcFalse) {
        printf("Failed to add font: %s\n", fontdesc);
        return 1;
    }

    FcConfigBuildFonts(FcConfigGetCurrent());

    // printf("Font added successfully: %s\n", fontdesc);
    return 0;
}
