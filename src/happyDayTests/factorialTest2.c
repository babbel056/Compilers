//  ********************************************
//  Authors: Jeroen Verstraelen - Anthony Hermans
//  Description: This program will calculate the factorial of a given number (non recursive)
//  ********************************************
#include <stdio.h>
int main(){
    int n;
    int i;
    int factorial = 1;
    printf("Enter an integer: ");
    scanf("%d",&n);
    if (n<0){
      printf("Factorial of negative number doesn't exist\n");
      return;
    }
    for(i=1; i<=n; i++){
      factorial = factorial*i;
    }
    printf("Factorial of %d = %d", n, factorial);
    return 0;
}
