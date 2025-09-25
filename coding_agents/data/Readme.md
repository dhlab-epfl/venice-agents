### Simplifications on `catastici` (buildings_1740) dataset
- numeric `an_rendi`
- `owner_count`=1
- `owner_code`='PPL'
- '_' not in `owner_first_name`
- removed NaN `owner_first_name` `tenant_name` `building_functions` `location`

#### Sample
|Owner_First_Name|Owner_Family_Name|Owner_Profession|Tenant_Name|Building_Functions|Rent_Price|Location|Parish|Building_Functions_Count|Longitude|Latitude|
|---|---|---|---|---|---|---|---|---|---|---|
|liberal|campi||francesco zeni|bottega, casa|70|campo vicino alla chiesa|san cancian|2|12.338315191259134|45.440397691052866|
|filippo|frari||dio m'aiuti lazara|casa|60|campo vicino alla chiesa|san cancian|1|12.338431859140826|45.44027817805552|
|filippo|frari||bortolamio piazza|bottega|4|campo vicino alla chiesa|san cancian|1|12.338492541778166|45.44031867953029|
|agostin|filippi||stefano ratti|bottega, casa|70|campo vicino alla chiesa|san cancian|2|12.338210776900992|45.44023535715787|
|ottavio|bertotti||rocco rimondi|magazzeno|22|campo vicino alla chiesa|san cancian|1|12.338224520594391|45.440222175120766|


### Simplifications on `sommarioni` (buildings_1808) dataset
- `parcel_type` = 'building'
- kept not null `own_uid`
- removed nan `building_functions`
- removed `district_acronym`='NCC'

#### Sample
|District|Location|Building_Area|Owner_Family_Name|Owner_First_Name|Building_Functions_Count|Building_Functions|Longitude|Latitude|
|---|---|---|---|---|---|---|---|---|
|san marco|parrocchia di s. fantino|168.644|todarini|ferdinando|1|casa|12.334534496043398|45.434012297059816|
|san marco|parrocchia di s. angelo|262.716|trevisani|giacomo|2|bottega, casa|12.33330436923513|45.4344001803324|
|san polo|calle dei varoteri detta di mezzo|28.589|de giacomi|giovanni battista|2|bottega, volta|12.335116690981442|45.43899193136069|
|san polo|sottoportico cordaria|30.108|coco|andrea|1|bottega|12.335040920361996|45.439100012005234|
|san polo|sottoportico cordaria|26.56|mocenigo|alvise|1|bottega|12.335069905675832|45.43908047778915|