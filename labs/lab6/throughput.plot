set ylabel "Throughput [Mbps]"
set xlabel "Time [second]"
set key bel
plot "tcp1.tr" u 1:2 t "tcp1" w lp lt rgb "blue", "tcp2.tr" u 1:2 t "tcp2" w lp lt rgb "red"

# set term png
# set output "throughput.png"
# replot
pause -1
