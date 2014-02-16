/* contest: Thumbtack Final 13-14
 * problem: Game
 * author: ksg
 *
 * Wrong solution
 * ?? / 100
 */

#include <cstdio>
#include <cstdlib>
#include <iostream>

using namespace std;

int main(int argc, char** argv) {

    long T;
    cin >> T;
    
    for (long t = 0; t < T; ++t) {
        long d, n, cur;
        long long ans = 1ll;
        scanf("%ld %ld", &d, &n);
        
        for (long i = 0; i < n; ++i) {
            scanf("%ld", &cur);
            ans *= (long long) (cur / d);
        }
        
        if(ans % 2)
            printf("First\n");
        else
            printf("Second\n");
    }
    
    return 0;
}

