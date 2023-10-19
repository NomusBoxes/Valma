vector_pairs = [((37.367672511831096, 22.824611927628467),
  (7.0804089150143135, 3.164616623307437)),
 ((30.175736625167293, 96.68532683271852),
  (32.730298963945806, 37.99316789038551)),
 ((21.39794809227854, 34.736729635767375),
  (83.7030864424463, 60.843614458619854)),
 ((77.65695335254212, 8.792129090163014),
  (90.557831089241, 18.635505924412456)),
 ((32.983300767109014, 78.29435395022126),
  (90.17188301532126, 39.85202894397305)),
 ((27.07865337196642, 57.36619776163899),
  (87.9718412893751, 92.19612587512984)),
 ((68.14138081331141, 19.290256936164607),
  (8.070862236234333, 49.154306586113485)),
 ((97.24562077408603, 77.53473629011137),
  (12.134780517503053, 20.30744389792597)),
 ((23.38161091457085, 60.13718258526409),
  (53.70274750609504, 17.347188737932516)),
 ((70.39670205411988, 77.65235433986429),
  (17.520857887789266, 94.182912744612)),
 ((38.90226595264069, 4.69929173134549),
  (42.02648068147764, 0.1752637278601754)),
 ((55.787835355382455, 41.23285673387234),
  (22.970831409767676, 13.832161863165126)),
 ((54.48609726535717, 24.47265680293714),
  (26.86236557306234, 93.74748233173908)),
 ((31.19428479771762, 70.24477727089075),
  (3.024962182927571, 37.75208850882373)),
 ((72.46421899726624, 55.11422693147024),
  (99.21480549601452, 15.96570614716577)),
 ((18.585017693643724, 69.27906796559016),
  (36.90741882175374, 41.840795818058176)),
 ((48.496579047838075, 59.41494606761086),
  (41.215873809964485, 3.5186156716384254)),
 ((89.05764867895095, 23.836430290315935),
  (55.18796173336167, 19.808012490594407)),
 ((21.168946729760265, 16.702796011730204),
  (48.330743096284145, 88.46882708957091)),
 ((14.69605962439684, 6.847547108396512),
  (86.48753101227139, 22.743459339096873)),
 ((59.51652273794677, 55.74943230849932),
  (16.461040829940842, 74.5198544767167)),
 ((97.50527062087964, 57.76285616427435),
  (13.329601656963408, 26.634038308652674)),
 ((7.3540321551815, 16.072764304889773),
  (1.2406859369726186, 88.43446180250078)),
 ((38.39039940653471, 79.97401257164897),
  (95.48867327630548, 65.55970294158121)),
 ((71.77655055182646, 48.49729054453222),
  (85.76005403553671, 64.67268656662692)),
 ((93.44329255414533, 82.61742328488924),
  (89.96253481005905, 22.003224028741464)),
 ((46.33076875277362, 24.055425453309056),
  (3.442503491876092, 50.39630521892903)),
 ((6.559260620353524, 68.62354296380761),
  (40.182353253900004, 71.93214880054609)),
 ((3.9145951386927114, 36.037281657468135),
  (4.774773848501212, 47.12772779189835)),
 ((95.73018361803216, 88.44345090277227),
  (62.439086655729206, 44.55797589793226))]


import matplotlib.pyplot as plt

# Plotting the vectors
plt.figure(figsize=(10, 10))
for start, end in vector_pairs:
    plt.arrow(start[0], start[1], end[0] - start[0], end[1] - start[1], 
              head_width=2, head_length=2, fc='blue', ec='blue')

plt.xlim(0, 100)
plt.ylim(0, 100)
plt.xlabel("X")
plt.ylabel("Y")
plt.title("Visualization of Vectors")
plt.grid(True)
plt.show()