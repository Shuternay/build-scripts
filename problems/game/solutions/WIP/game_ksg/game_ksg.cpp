/* contest: Thumbtack Final 13-14
 * problem: Game
 * author: ksg
 *
 * Correct solution
 * 100 / 100
 */

#include <cstdio>
#include <cstdlib>
#include <iostream>

using namespace std;

int main(int argc, char** argv) {
    //freopen("input.txt", "r", stdin);
    //freopen("output.txt", "w", stdout);
    long T;
    cin >> T;
    
    for (long t = 0; t < T; ++t) {
        long d, n, cur, ans = 1;
        scanf("%ld %ld", &d, &n);
        
        for (long i = 0; i < n; ++i) {
            scanf("%ld", &cur);
            if(cur < d)
                ans = 0;
        }
        
        if(ans)
            printf("First\n");
        else
            printf("Second\n");
    }
    
    return 0;
}

