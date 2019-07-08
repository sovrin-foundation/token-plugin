# Fees related auth_rule
The next authorization rule extends default auth_map from indy-node ([auth_map](https://github.com/hyperledger/indy-node/blob/master/docs/source/add-node.md))
<table class="tg">
  <tr>
    <th>Transaction type</th>
    <th>Action</th>
    <th>Field</th>
    <th>Previous value</th>
    <th>New value</th>
    <th>Who can</th>
    <th>Description</th>
  </tr>

  <tr>
    <td>SET_FEES</td>
    <td>EDIT</td>
    <td>*</td>
    <td>*</td>
    <td>*</td>
    <td>3 TRUSTEEs</td>
    <td>Setting fees for action/actions</td>
  </tr>