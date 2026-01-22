import java.util.Scanner;

public class Solution {
    private static final Scanner scanner = new Scanner(System.in);

    public static void main (String[] args) { 
        int N = scanner.nextInt();
        scanner.close();

        if (N%2 ==0){
            if(N>=6 && N<=20){
                System.out.println("weird");
            }

        }
    }
}

