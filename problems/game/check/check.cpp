#include "testlib.h"
#include <string>

using namespace std;

const string YES = "FIRST";
const string NO = "SECOND";

int main(int argc, char * argv[]) {
    setName("check answer for problem Game from Thumbtack Cup 13-14 Final");
    registerTestlibCmd(argc, argv);

    long n = 0;
    string ja, pa;
    
    while (!ans.seekEof() && !ouf.seekEof()) {
        n++;

        ja = upperCase(ans.readWord());
        pa = upperCase(ouf.readWord());


        if (ja != YES && ja != NO)
            quitf(_fail, "%ld%s word in answer incorrect - %s or %s expected, but %s found",
                    n, englishEnding(n).c_str(),YES.c_str(), NO.c_str(), compress(ja).c_str());

        if (pa != YES && pa != NO)
            quitf(_pe, "%ld%s word incorrect - %s or %s expected, but %s found",
                    n, englishEnding(n).c_str(),YES.c_str(), NO.c_str(), compress(pa).c_str());

        if (ja != pa)
            quitf(_wa, "%ld%s words differ - expected: '%s', found: '%s'",
                    n, englishEnding(n).c_str(), compress(ja).c_str(), compress(pa).c_str());
    }

    if (ans.seekEof() && ouf.seekEof()) {
        if (n == 1)
            quitf(_ok, "\"%s\"", compress(ja).c_str());
        else
            quitf(_ok, "%ld tokens", n);
    } else {
        if (ans.seekEof())
            quitf(_wa, "Participant output contains extra tokens");
        else
            quitf(_wa, "Unexpected EOF in the participants output");
    }

}
